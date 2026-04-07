# Project Memory — aicli
_Generated: 2026-04-07 17:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform providing Claude CLI and Electron desktop interfaces for AI-assisted project management. It captures developer activity (prompts, commits, documents) through a 4-layer memory pipeline (raw capture → LLM digests → structured work items/facts → user-managed planner tags), with PostgreSQL pgvector backend for semantic search, FastAPI REST API, and async DAG workflow execution. Currently addressing backend query performance optimization and frontend UI consistency issues around work item management and tag drag-and-drop interactions.

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

### `commit` — 2026-04-07

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 93632e3..33b9811 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway initial load slow (~60s per round-trip, 0.9s per query), but functional
+- Schema cleanup: removed diff_summary and source_session_id columns from work item commit queries; verified migration 008 dropped these fields and memory_planner.py now uses tags['files'] dict instead
+- Backend data loading optimization: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS) and line 288 (merged_into/start_date alignment) under investigation; Railway migrations functional but slow (~60s per round-trip, 0.9s per query)
 - Work item drag-and-drop UI refinement: fixing hover state propagation for target tag highlights; ensuring dropped work items persist in correct parent and disappear from source after page reload
 - Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
-- Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table display
-- Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification
 - Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage
+- Mirror table architecture investigation: understanding trigger mechanisms for mem_ai_events and mem_ai_project_facts, LLM prompts used in synthesis, and data flow from session commits/events


### `commit` — 2026-04-07

diff --git a/workspace/_templates/aicli_memory.md b/workspace/_templates/aicli_memory.md
deleted file mode 100644
index 6c388ce..0000000
--- a/workspace/_templates/aicli_memory.md
+++ /dev/null
@@ -1,331 +0,0 @@
-# aicli Memory Pipeline — Architecture Reference
-
-_Last updated: 2026-04-07 · Version 2.3.0_
-
----
-
-## Overview
-
-The aicli memory pipeline is a 4-layer system that captures developer activity (prompts, commits,
-documents, messages), digests it with Haiku, embeds it with OpenAI, and promotes structured
-artifacts (work items, project facts) upward toward human-managed planner tags.
-
-```
-Developer activity
-      │
-      ▼
-┌─────────────────────────────────────────────────────────┐
-│  Layer 0 — Source Trigger                               │
-│  Hook scripts → POST /memory/* endpoints                │
-└──────────────────────────┬──────────────────────────────┘
-                           │
-                           ▼
-┌─────────────────────────────────────────────────────────┐
-│  Layer 1 — Mirror (mem_mrr_*)                           │
-│  Raw data verbatim, inline tags JSONB                   │
-└──────────────────────────┬──────────────────────────────┘
-                           │ MemoryEmbedding.process_*()
-                           ▼
-┌─────────────────────────────────────────────────────────┐
-│  Layer 2 — AI Events (mem_ai_events)                    │
-│  Haiku digest + OpenAI embedding + importance score     │
-└──────────────────────────┬──────────────────────────────┘
-                           │ MemoryPromotion.*()
-                           ▼
-┌─────────────────────────────────────────────────────────┐
-│  Layer 3 — Structured Artifacts                         │
-│  mem_ai_work_items  ·  mem_ai_project_facts             │
-└──────────────────────────┬──────────────────────────────┘
-                           │ User drag-drop / Planner button
-                           ▼
-┌─────────────────────────────────────────────────────────┐
-│  Layer 4 — User-Managed Tags (planner_tags)             │
-│  Features · Bugs · Tasks — owned by users               │
-└─────────────────────────────────────────────────────────┘
-```
-
----
-
-## Layer 1 — Mirror Tables (`mem_mrr_*`)
-
-### `mem_mrr_prompts` — Raw prompt/response pairs
-
-**Trigger**: Hook script `post_prompt.sh` → `POST /memory/{project}/prompts`
-**Responsible**: Trigger (auto, no LLM)
-
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `id` | Trigger | UUID PK |
-| `session_id` | Trigger | Groups turns in a session |
-| `source_id` | Trigger | External ID from hook |
-| `prompt` | Trigger | Raw user input |
-| `response` | Trigger | Raw AI response |
-| `tags` | Trigger | Inline JSONB: `{source, phase, feature, work-item, llm}` |
-| `created_at` | Trigger | Insert timestamp |
-
-**Relevance score**: 0/5 — raw data, no digest yet; useful only as source for Layer 2
-
----
-
-### `mem_mrr_commits` — Raw git commits
-
-**Trigger**: Post-commit hook `post_commit.sh` → `POST /memory/{project}/commits`
-**Responsible**: Trigger (auto, no LLM initially)
-
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `commit_hash` | Trigger | PK |
-| `commit_msg` | Trigger | Git commit message |
-| `summary` | **LLM** (back-propagated) | Haiku digest back-written by `process_commit()` |
-| `tags` | Trigger + LLM | Initial: `{source, phase, feature}`; LLM adds `files`, `languages`, `symbols` |
-| `session_id` | Trigger | Links to session |
-| `committed_at` | Trigger | Git timestamp |
-
-**`tags["files"]`**: `{filename: rows_changed}` — populated by `smart_chunk_diff()` from actual diff
-**`tags["symbols"]`**: class/function names from diff (Python/JS/TS) — populated by code symbol extraction
-**`tags["languages"]`**: list of languages in diff — populated by `_detect_language()`
-
-**Relevance score**: 3/5 — commit message is useful; summary + files/symbols make it 4/5
-
----
-
-### `mem_mrr_items` — Documents, requirements, decisions
-
-**Trigger**: Manual `POST /memory/{project}/items` or CLI import
-**Responsible**: User (creates) + LLM (digests)
-
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `id` | Trigger | UUID PK |
-| `item_type` | User | `requirement`, `decision`, `meeting`, `note` |
-| `title` | User | Short title |
-| `raw_text` | User | Full document content |
-| `summary` | **LLM** | Haiku digest (back-propagated if short item) |
-| `tags` | User | Inline JSONB classification |
-
-**Relevance score**: 4/5 — decisions and requirements are high-value; meeting notes 3/5
-
----
-
-### `mem_mrr_messages` — Platform messages (Slack, Teams)
-
-**Trigger**: Integration hook → `POST /memory/{project}/messages`
-**Responsible**: Trigger (auto)
-
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `id` | Trigger | UUID PK |
-| `platform` | Trigger | `slack`, `teams`, `discord` |
-| `channel` | Trigger | Channel/thread name |
-| `messages` | Trigger | JSONB array of `{user, text, ts}` |
-| `tags` | Trigger | Session/feature classification |
-
-**Relevance score**: 2/5 — discussion context; useful when linked to features
-
----
-
-## Layer 2 — AI Events (`mem_ai_events`)
-
-**Trigger**: `MemoryEmbedding.process_*()` — called after each mirror INSERT
-**Responsible**: LLM (digest + importance) + Trigger (embedding)
-
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `id` | Trigger | UUID PK |
-| `event_type` | Trigger | `prompt_batch`, `commit`, `item`, `message`, `session_summary`, `workflow` |
-| `source_id` | Trigger | FK to mirror row |
-| `session_id` | Trigger | Propagated from mirror |
-| `chunk` | Trigger | 0=summary/digest, 1+=detail chunks |
-| `chunk_type` | Trigger | `full`, `summary`, `section`, `diff_file`, `class`, `function` |
-| `content` | **LLM** | Haiku digest text (chunk=0); raw diff/code (chunk>0) |
-| `summary` | **LLM** | Haiku 1-2 sentence summary |
-| `action_items` | **LLM** | Extracted

### `commit` — 2026-04-07

diff --git a/aicli_memory.md b/aicli_memory.md
index 605c687..ca019f2 100644
--- a/aicli_memory.md
+++ b/aicli_memory.md
@@ -1,663 +1,391 @@
 # aicli — Memory & Tagging Architecture
 
-_Last updated: 2026-04-01 | Full rewrite — covers all 5 layers, tagging flows, Planner UI, issues, and refactoring advice_
+_Last updated: 2026-04-07 | Updated for migration 014 + importance scoring + auto-extract pipeline_
 
 ---
 
 ## 0. Mental Model
 
-aicli memory has **5 layers** stacked on top of each other.
-**Tagging is a separate, orthogonal system** that cuts across all layers to connect everything.
+aicli memory has **4 active layers** stacked on top of each other.
+**planner_tags** is the user-managed top layer; everything below is LLM/trigger-managed.
 
 ```
  ┌──────────────────────────────────────────────────────────────────────┐
  │ Layer 0 — Ephemeral         In-session message list (RAM / JSON)     │
  │ Layer 1 — Raw Capture       Everything stored as-is   (mem_mrr_*)    │
  │ Layer 2 — AI Events         Digested + embedded        (mem_ai_events)│
- │ Layer 3 — Structured        Facts / Work Items / Snapshots           │
- │ Layer 4 — Context Files     CLAUDE.md, .cursorrules, llm_prompts/    │
- └──────────────────────────────────────────────────────────────────────┘
-
- ┌──────────────────────────────────────────────────────────────────────┐
- │ Tagging (orthogonal)        planner_tags + mem_mrr_tags + mem_ai_tags│
+ │ Layer 3 — Structured        Work Items + Project Facts                │
+ │ Layer 4 — User Tags         planner_tags  (USER-MANAGED)              │
  └──────────────────────────────────────────────────────────────────────┘
 ```
 
+**Key design principle**:
+- `planner_tags` = **User** owns this. LLM only writes when user clicks "Run Planner" or "Snapshot".
+- Everything below `planner_tags` = **LLM + Triggers** own it. User does not manually edit.
+- `tag_id` on work items = **User** sets via drag-drop only. `ai_tag_id` = LLM suggestion (auto).
+
 ---
 
 ## Layer 0 — Ephemeral (Session Messages)
 
-**What it is**: The live `messages[]` array forwarded to the LLM on every turn.
-
+**Responsible**: Trigger (auto, no DB)
 **Storage**: `workspace/{project}/_system/sessions/{session_id}.json`
 **Python class**: `SessionStore` (`backend/memory/mem_sessions.py`)
-**NOT stored in PostgreSQL** — file-only, short-lived.
-
-**Schema (per JSON file)**:
-```json
-{
-  "id": "uuid",
-  "created_at": "iso",
-  "updated_at": "iso",
-  "messages": [
-    { "role": "user|assistant", "content": "...", "ts": "iso" }
-  ],
-  "metadata": { "phase": "...", "feature": "...", "bug_ref": "..." }
-}
-```
 
-**Trigger**: Every API request that calls `SessionStore.append_message()`.
-
-**Purpose**: Maintain conversation continuity within a session. Has nothing to do with the DB pipeline.
+Not stored in PostgreSQL — file-only, short-lived within a session.
 
 ---
 
 ## Layer 1 — Raw Capture (`mem_mrr_*`)
 
-**What it is**: Everything stored exactly as received. No AI processing. Acts as the source-of-truth audit trail.
-
-### Tables
+Everything stored verbatim as received. No AI processing. The audit trail.
 
-| Table | PK | Key columns | Written by |
-|-------|----|-------------|-----------|
-| `mem_mrr_prompts` | `id UUID` | project, session_id, prompt TEXT (≤4000), response TEXT (≤8000), source_id, llm_source, phase, ai_tags, work_item_id FK→mem_ai_work_items | `log_user_prompt.sh` hook → `POST /chat/{p}/hook-log` |
-| `mem_mrr_commits` | `commit_hash VARCHAR(64)` | project, commit_msg, diff_summary, diff_details JSONB, session_id, phase, feature, bug_ref, ai_tags, committed_at | `auto_commit_push.sh` hook → `POST /git/{p}/commit-push` |
-| `mem_mrr_items` | `id UUID` | project, item_type ('requirement'/'decision'/'meeting'), title, raw_text, summary, meeting_at, attendees TEXT[], ai_tags | Item ingest API (`POST /history/items`) |
-| `mem_mrr_messages` | `id UUID` | project, platform ('slack'/'teams'/'discord'), channel, thread_ref, messages JSONB, date_range TSTZRANGE, ai_tags | Platform connector API |
+### `mem_mrr_prompts`
 
-**The `ai_tags` lifecycle** (on all 4 tables):
-```
-NULL          → row arrived, not yet processed by AI tagging pipeline
-'approved'    → AI suggested a tag, user accepted it
-'ignored'     → AI suggested a tag, user rejected it
-```
+**Trigger**: `post_prompt.sh` hook → `POST /memory/{p}/prompts`
 
-**Python class**: `MemoryMirroring` (`backend/memory/memory_mirroring.py`)
-Key methods: `store_prompt()`, `store_commit()`, `store_item()`, `store_message()`, `get_untagged()`, `set_ai_tag_status()`
+| Column | Responsible | Notes |
+|--------|-------------|-------|
+| `id` UUID | Trigger | PK |
+| `session_id` | Trigger | Groups turns in a session |
+| `source_id` | Trigger | External ID from hook |
+| `prompt` TEXT | Trigger | Raw user input |
+| `response` TEXT | Trigger | Raw AI response |
+| `tags` JSONB | Trigger | `{source, phase, feature, work-item, llm}` — inline tagging |
+| `created_at` | Trigger | Insert timestamp |
 
-**Idempotent**: All inserts use ON CONFLICT patterns — safe to replay.
+**Relevance: 0/5** — raw data, no digest; only useful as source for Layer 2
 
 ---
 
-## Layer 2 — AI Events (`mem_ai_events`)
+### `mem_mrr_commits`
 
-**What it is**: Every Layer 1 source gets digested by Haiku and embedded into a 1536-dim vector. This is the primary semantic search target.
-
-### Table: `mem_ai_events`
-
-| Column | Type | Notes |
-|--------|------|-------|
-| id | UUID PK | |
-| client_id | INT | |
-| project | VARCHAR | |
-| event_type | TEXT | `'prompt_batch'` \| `'commit'` \| `'item'` \| `'message'` \| `'session_summary'` \| `'workflow'` |
-| source_id | TEXT | UUID, commit hash, or session_id depending on event_type |
-| session_id | TEXT | Session that produced this event |
-| llm_source | VARCHAR(100) | Model that created the digest (e.g. `claude-haiku-4-5-20251001`) |
-| chunk | INT | 0 = full; >0 = multi-part (large docs/commits split into secti

### `commit` — 2026-04-07

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 0f54796..c05702d 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-07 15:05 UTC
+> Generated by aicli 2026-04-07 16:44 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-04-07

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index ffcae6a..0e2d1ac 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 15:05 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 16:44 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -64,8 +64,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-06] I would like to be able to move work_item back to work_item or to another items. also merge - merge can happend only to 
 - [2026-04-07] can you update all memory_items (maybe run /memory) to have an uodated data
 - [2026-04-07] I do have some errors loading data - route_work_items line 249 - cur.execute(_SQL_UNLINKED_WORK_ITEMS, (p_id,)) and line
 - [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
-- [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
\ No newline at end of file
+- [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
+- [2026-04-07] In addtion to your reccomendation, I would like to check the following -  mem_ai_coomits -  what is diff_details is used
\ No newline at end of file


### `commit` — 2026-04-07

diff --git a/.ai/rules.md b/.ai/rules.md
index ffcae6a..0e2d1ac 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 15:05 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 16:44 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -64,8 +64,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-06] I would like to be able to move work_item back to work_item or to another items. also merge - merge can happend only to 
 - [2026-04-07] can you update all memory_items (maybe run /memory) to have an uodated data
 - [2026-04-07] I do have some errors loading data - route_work_items line 249 - cur.execute(_SQL_UNLINKED_WORK_ITEMS, (p_id,)) and line
 - [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
-- [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
\ No newline at end of file
+- [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
+- [2026-04-07] In addtion to your reccomendation, I would like to check the following -  mem_ai_coomits -  what is diff_details is used
\ No newline at end of file


## AI Synthesis

**[2026-04-07]** `git_schema` — Confirmed commit table schema: `diff_summary` (TEXT) retained as human-readable git --stat; `diff_details` (JSONB) dropped and removed from mcp/server.py and memory_mirroring.py references. **[2026-04-07]** `memory_architecture` — Finalized 4-layer memory model: Layer 1 (mem_mrr_* raw capture) → Layer 2 (mem_ai_events LLM digests + 1536-dim embeddings) → Layer 3 (mem_ai_work_items, mem_ai_project_facts structured artifacts) → Layer 4 (planner_tags user-managed). **[2026-04-07]** `backend_optimization` — Identified route_work_items bottleneck: _SQL_UNLINKED_WORK_ITEMS (line 249) and merged_into/start_date column alignment (line 288) causing 60s round-trip latency on Railway; individual queries execute in ~0.9s, suggesting N+1 or connection pool issue. **[2026-04-07]** `frontend_refactor` — Targeting _plannerSelectAiSubtype undefined reference error in routers.route_logs; requires proper function scoping and global export of all planner helper functions. **[2026-04-01]** `schema_migration` — Migration 008 successfully dropped diff_summary and source_session_id columns from work item queries; memory_planner.py refactored to use tags['files'] dict instead of deprecated columns. **[2026-04-01]** `ui_drag_drop` — Work item drag-and-drop refinement in progress: fixing hover state propagation for target tag highlights and ensuring persistence across page reloads.