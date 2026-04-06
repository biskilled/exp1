# Project Memory — aicli
_Generated: 2026-04-06 12:59 UTC by aicli /memory_

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
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) + JSONB UNION batch upsert
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) with JSONB UNION batch upsert queries
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- PostgreSQL batch upsert with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Commit deduplication by hash with UNION consolidation across multiple sources; commits linked per-prompt with inline display (accent left-border)
- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation

## In Progress

- PostgreSQL batch upsert JSONB type casting: resolved execute_values error via explicit ::jsonb casting for tags field; commit deduplication via seen dict to prevent ON CONFLICT DO UPDATE processing same hash twice
- Commit sync and deduplication: /history/commits/sync endpoint imports unique commit hashes with proper prompt linkage; commit message truncation fixed to support full metadata display
- History display dual-hook architecture verification: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis activation
- Memory items and project_facts table population: enable event-based triggering with differentiated process_item/messages handling for core memory functionality activation
- MEMORY.md and aicli_memory.md documentation gap: tables in MEMORY.md updated to reflect current schema (mem_ai_* tables); comprehensive memory architecture documentation covering all layers, mirroring mechanisms, event triggers, and processing prompts
- Copy-to-clipboard functionality: text selection and copying capability in history UI for improved usability and better content accessibility

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

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 3395bf1..751567d 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -51,10 +51,10 @@
     "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
     "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev",
     "Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling",
-    "Phase persistence with red \u26a0 badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking",
-    "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u21a9 link) showing only that prompt's commits",
     "PostgreSQL batch upsert JSONB with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE",
-    "Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention"
+    "Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention",
+    "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u21a9 link) showing only that prompt's commits",
+    "Phase persistence with red \u26a0 badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking"
   ],
   "implemented_features": [
     "5-layer memory architecture with /memory endpoint + LLM synthesis via Haiku",
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-06T10:22:23Z",
+  "last_memory_run": "2026-04-06T10:22:45Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files",
@@ -134,10 +134,10 @@
       "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
       "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev",
       "Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling",
-      "Phase persistence with red \u26a0 badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking",
-      "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u21a9 link) showing only that prompt's commits",
       "PostgreSQL batch upsert JSONB with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE",
-      "Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention"
+      "Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention",
+      "Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash \u21a9 link) showing only that prompt's commits",
+      "Phase persistence with red \u26a0 badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking"
     ],
     "in_progress": [
       "PostgreSQL batch upsert JSONB fix: resolved ON CONFLICT DO UPDATE duplicate row insertion error with explicit ::jsonb casting for tags field",
@@ -153,25 +153,17 @@
       "frontend": "Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server",
       "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
       "storage_primary": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-      "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-      "database_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
       "authentication": "JWT (python-jose + bcrypt) + DEV_MODE toggle",
       "llm_providers": "Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok",
       "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic",
-      "workflow_ui": "Cytoscape.js + cytoscape-dagre; 2-pane approval panel",
       "memory_synthesis": "Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions",
       "chunking": "Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)",
       "mcp": "Stdio MCP server with 12+ tools",
-      "config_management": "config.py + YAML pipelines + pyproject.toml",
-      "billing_storage": "data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables",
-      "backend_modules": "routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server",
-      "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root",
-    

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 5b944cd..cc2e17b 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-06T10:22:32Z",
+  "last_updated": "2026-04-06T10:52:44Z",
   "last_session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c",
-  "last_session_ts": "2026-04-06T10:22:32Z",
-  "session_count": 384,
+  "last_session_ts": "2026-04-06T10:52:44Z",
+  "session_count": 385,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 25a8335..ba439f5 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -57,7 +57,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
-- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
 - PostgreSQL batch upsert JSONB with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
 - Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
+- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 227a193..08fc0ef 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -685,3 +685,5 @@
 {"ts": "2026-04-06T09:57:55Z", "action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "39500d7a", "message": "docs: update AI system context and memory files post-session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "20807f33", "message": "docs: update system context and memory files after CLI session", "files_count": 64, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T10:22:10Z"}
 {"ts": "2026-04-06T10:22:07Z", "action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "20807f33", "message": "docs: update system context and memory files after CLI session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "56a57ca3", "message": "docs: clean up system context and memory files after claude session", "files_count": 61, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T10:22:36Z"}
+{"ts": "2026-04-06T10:22:32Z", "action": "commit_push", "source": "claude_cli", "session_id": "b9e39fae-45bf-482c-a3e9-fa65ed840b6c", "hash": "56a57ca3", "message": "docs: clean up system context and memory files after claude session", "pushed": true, "push_error": ""}


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index abdc2ed..969822f 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -5,7 +5,7 @@ _Generated: 2026-04-06 10:22 UTC by aicli /memory_
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + PostgreSQL + pgvector) with an Electron desktop frontend (Vanilla JS + Cytoscape), enabling teams to manage AI-assisted workflows through semantic memory synthesis, multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok), and async DAG-based pipeline execution. The platform is currently in v2.2.0 with recent focus on fixing data persistence layers (JSONB upserts), completing commit history synchronization from git, and enabling memory layer event triggering for project facts and work item consolidation.
+aicli is a shared AI memory platform combining a Python FastAPI backend, PostgreSQL semantic storage (pgvector), and an Electron desktop UI for collaborative AI-driven development workflows. It synthesizes project context into structured memory (events, facts, work items, features) using Claude Haiku dual-layer analysis, supports multi-LLM providers, and executes async DAG workflows with visual approval panels. Currently stabilizing database upsert logic, commit synchronization, and memory synthesis triggers while expanding UI usability (copy-to-clipboard, full commit metadata display).
 
 ## Tech Stack
 
@@ -57,10 +57,10 @@ aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + P
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
-- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
 - PostgreSQL batch upsert JSONB with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
 - Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
+- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
 
 ## In Progress
 
@@ -73,4 +73,13 @@ aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + P
 
 ## AI Synthesis
 
-**[2026-03-14]** `db-fix` — Resolved PostgreSQL batch upsert JSONB duplicate row insertion error by adding explicit ::jsonb casting to tags field in ON CONFLICT DO UPDATE clause. **[2026-03-14]** `commit-sync` — Implemented /history/commits/sync endpoint successfully importing 364+ unique commit hashes from multiple sources with proper prompt-to-commit linkage and deduplication logic. **[2026-03-14]** `ui-display` — Fixed commit message truncation in commits tab; verified database schema supports complete commit metadata storage and frontend display. **[2026-03-14]** `memory-hooks` — Validated dual-hook architecture where hook-response and session-summary hooks correctly persist both user prompts and LLM responses to mem_mrr_prompts table. **[2026-03-14]** `memory-population` — Enabled event-based triggering for memory items and project_facts with differentiated process_item vs. messages handling for core memory synthesis functionality. **[2026-03-14]** `ux-enhancement` — Identified copy-to-clipboard functionality gap in history UI; prioritized implementation of text selection and copy capability for improved user workflow.
\ No newline at end of file
+**[2026-03-14]** `PostgreSQL` — Fixed ON CONFLICT DO UPDATE duplicate row insertion error by adding explicit ::jsonb casting for tags field in batch upsert queries.
+**[2026-03-14]** `Commit Sync` — Implemented /history/commits/sync endpoint to import 364+ unique commit hashes with proper prompt linkage and deduplication logic.
+**[2026-03-14]** `UI/History` — Fixed commit message truncation in commits tab to ensure complete metadata displays; verified dual-hook architecture saves prompts and responses to mem_mrr_prompts.
+**[2026-03-14]** `Memory Layer` — Enabled event-based triggering for memory items and project_facts population with differentiated process_item/messages handling.
+**[2026-03-14]** `Startup Robustness` — Resolved backend race condition on first load with retry_logic_handles_empty_project_list and _ensure_shared_schema consolidation.
+**[2026-03-14]** `Phase & Tags` — Implemented red ⚠ badge for missing phase; auto-saved tag suggestions via _acceptSuggestedTag with distinct visual marking.
+**[2026-03-14]** `Data Persistence` — Standardized load_once_on_access, update_on_save pattern; session ordering by created_at to prevent reordering on tag/phase updates.
+**[2026-03-14]** `Commit Display` — Added commit-per-prompt inline display with accent left-border and hash ↩ links showing only that prompt's commits.
+**[2026-03-14]** `Chunking Strategy` — Smart chunking per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs) with manual relations via CLI/admin UI.
+**[2026-03-14]** `Deployment & CLI` — Unified deployment across Railway cloud (Dockerfile + railway.toml), Electron-builder desktop, and local bash/npm startup scripts.
\ No newline at end of file


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index bd2e19f..66a893e 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -37,10 +37,10 @@ You are a senior Python software architect with deep expertise in:
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
-- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
 - PostgreSQL batch upsert JSONB with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
 - Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
+- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
 
 ---
 

