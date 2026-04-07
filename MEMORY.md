# Project Memory — aicli
_Generated: 2026-04-07 16:48 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend, PostgreSQL vector storage, and Electron desktop UI to enable semantic project memory synthesis via Claude Haiku. The system uses async DAG workflows, work item management with dual-status tracking, and intelligent chunking to maintain context across collaborative development sessions. Currently in active development with focus on performance optimization, UI refinement for drag-and-drop interactions, and completion of memory synthesis trigger architecture.

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
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
- Session-level UI consolidation: Planner tab unified for all tag management with category/status/properties; suggested tags marked distinctly
- Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables
- Project facts generated via LLM prompt analyzing session events and commits; stored in mem_ai_project_facts with event_id linkage for traceability

## In Progress

- Schema cleanup: removed diff_summary and source_session_id columns from work item commit queries; verified migration 008 dropped these fields and memory_planner.py now uses tags['files'] dict instead of deprecated columns
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

diff --git a/workspace/aicli/documents/feature/shared-memory.md b/workspace/aicli/documents/feature/shared-memory.md
new file mode 100644
index 0000000..32a9f27
--- /dev/null
+++ b/workspace/aicli/documents/feature/shared-memory.md
@@ -0,0 +1,46 @@
+# feature: shared-memory
+_Last updated: 2026-04-07 · Project: aicli_
+
+## Use Case Summary
+Implement shared memory functionality to enable safe inter-process/inter-thread communication. Currently in early planning stages with requirements and technical specifications defined but no implementation or commit history yet.
+
+## Work Items (1)
+
+### #None memory · active
+_Prompts: 0 · ~0 words · 0 commits · Started: —_
+
+This work item tracks the implementation of shared memory functionality. Currently in early planning with no committed implementation. Requires detailed specification of memory management, synchronization primitives, and API design before development can begin. Will need comprehensive testing across concurrent access patterns.
+
+**Remaining:** Define detailed requirements for shared memory API
+Design synchronization and safety mechanisms
+Implement core shared memory module
+Write unit and integration tests
+Document API and usage patterns
+
+
+---
+
+## What Was Done
+- Identified core acceptance criteria for shared memory initialization and concurrent access
+
+## What Remains
+- Define detailed functional requirements and API specifications for shared memory interface
+- Design synchronization mechanisms and thread-safety guarantees
+- Implement core shared memory module with memory allocation/deallocation
+- Develop unit and integration tests covering concurrent access scenarios
+- Create comprehensive API documentation and usage examples
+- Perform cross-module integration testing and performance benchmarking
+
+## Acceptance Criteria
+- [ ] Shared memory can be initialized and accessed safely across multiple processes/threads
+- [ ] Memory allocation and deallocation complete without errors or resource leaks
+- [ ] Concurrent read/write operations maintain data integrity under stress testing
+- [ ] Performance benchmarks meet or exceed project SLAs
+
+## Files Changed
+| File | +Added | -Removed |
+|------|--------|------|
+| — | — | — |
+
+---
+_Auto-generated by aicli Planner · 2026-04-07 16:43 UTC_


### `prompt_batch: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

A diagnostic review of `mem_ai_commits` revealed that `diff_details` column should be removed (stores only documentation changes, not actual code diffs), and the row delta (+/-) metrics lack actionable data—the hook is logging correctly but the column design needs refinement to capture meaningful code change statistics.

### `commit` — 2026-04-07

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 1391d23..93632e3 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway migration takes 60+ seconds per round-trip, backend functional but slow on initial load
-- Work item drag-and-drop UI refinement: fixing hover state propagation so only target tag highlights; ensuring dropped work items persist in correct parent and disappear from source list after page reload
-- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions are properly scoped and exported to global scope
-- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage
-- Mirror table architecture investigation: understanding trigger mechanisms for mem_ai_events and mem_ai_project_facts, LLM prompts used in synthesis, and data flow from session commits/events
+- Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway initial load slow (~60s per round-trip, 0.9s per query), but functional
+- Work item drag-and-drop UI refinement: fixing hover state propagation for target tag highlights; ensuring dropped work items persist in correct parent and disappear from source after page reload
+- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
+- Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table display
 - Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification
+- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage


### `commit` — 2026-04-07

diff --git a/workspace/_templates/memory/prompts.yaml b/workspace/_templates/memory/prompts.yaml
index f9e5a6f..3452f8a 100644
--- a/workspace/_templates/memory/prompts.yaml
+++ b/workspace/_templates/memory/prompts.yaml
@@ -4,24 +4,30 @@
 
 - name: commit_digest
   category: memory
-  description: "Digest a git commit into 1-2 sentences"
+  description: "Digest a git commit into 1-2 sentences with importance score"
   content: |
-    Given a git commit message and diff summary, produce a 1-2 sentence digest capturing what changed and why.
-    Return plain text only, no preamble.
+    Given a git commit message and context, produce a concise digest.
+    Return JSON only: {"summary": "1-2 sentence digest of what changed and why", "action_items": "", "importance": 5}
+    importance scale (0-10): 1-2=trivial/chore, 3-4=minor fix, 5-6=feature work, 7-8=significant change, 9-10=critical/architectural
+    No preamble, no markdown fences.
 
 - name: prompt_batch_digest
   category: memory
-  description: "Digest N prompt/response pairs into 1-2 sentences"
+  description: "Digest N prompt/response pairs into 1-2 sentences with importance score"
   content: |
-    Given N sequential prompt/response pairs, extract a 1-2 sentence digest capturing what was decided, built, or discovered.
-    Return plain text only, no preamble.
+    Given N sequential prompt/response pairs, extract a digest capturing what was decided, built, or discovered.
+    Return JSON only: {"summary": "1-2 sentence digest", "action_items": "- bullet list of open action items, or empty string", "importance": 5}
+    importance scale (0-10): 1-2=trivial/chore, 3-4=debug/minor, 5-6=feature implementation, 7-8=architectural decision, 9-10=critical system design
+    No preamble, no markdown fences.
 
 - name: item_digest
   category: memory
-  description: "Summarise a document item in 1-2 sentences"
+  description: "Summarise a document item in 1-2 sentences with importance score"
   content: |
-    Summarise this document (requirement, decision, or note) in 1-2 sentences.
-    Return plain text only.
+    Summarise this document (requirement, decision, or note).
+    Return JSON only: {"summary": "1-2 sentence digest", "action_items": "- bullet list or empty string", "importance": 5}
+    importance scale (0-10): 1-2=reference/notes, 3-4=minor, 5-6=decision, 7-8=key requirement, 9-10=critical constraint
+    No preamble, no markdown fences.
 
 - name: meeting_sections
   category: memory
@@ -186,6 +192,20 @@
     }
     Focus on concrete decisions and code changes. Skip small talk and tool noise.
 
+- name: work_item_extraction
+  category: memory
+  description: "Extract actionable work items from a session digest"
+  content: |
+    You are a project memory analyst. Given a digest of recent development activity,
+    identify actionable work items: bugs to fix, features to build, tasks to complete.
+    Return JSON only:
+    {"items": [
+      {"category": "bug|feature|task", "name": "short-slug", "description": "1-2 sentence explanation"}
+    ]}
+    Return at most 5 items. Use lowercase-hyphenated slugs for name.
+    Return {"items": []} if nothing actionable is found.
+    No preamble, no markdown fences.
+
 # Legacy aliases (kept for backward compatibility with existing DB queries)
 - name: memory_batch_digest
   category: memory


### `commit` — 2026-04-07

diff --git a/workspace/_templates/aicli_memory.md b/workspace/_templates/aicli_memory.md
new file mode 100644
index 0000000..6c388ce
--- /dev/null
+++ b/workspace/_templates/aicli_memory.md
@@ -0,0 +1,331 @@
+# aicli Memory Pipeline — Architecture Reference
+
+_Last updated: 2026-04-07 · Version 2.3.0_
+
+---
+
+## Overview
+
+The aicli memory pipeline is a 4-layer system that captures developer activity (prompts, commits,
+documents, messages), digests it with Haiku, embeds it with OpenAI, and promotes structured
+artifacts (work items, project facts) upward toward human-managed planner tags.
+
+```
+Developer activity
+      │
+      ▼
+┌─────────────────────────────────────────────────────────┐
+│  Layer 0 — Source Trigger                               │
+│  Hook scripts → POST /memory/* endpoints                │
+└──────────────────────────┬──────────────────────────────┘
+                           │
+                           ▼
+┌─────────────────────────────────────────────────────────┐
+│  Layer 1 — Mirror (mem_mrr_*)                           │
+│  Raw data verbatim, inline tags JSONB                   │
+└──────────────────────────┬──────────────────────────────┘
+                           │ MemoryEmbedding.process_*()
+                           ▼
+┌─────────────────────────────────────────────────────────┐
+│  Layer 2 — AI Events (mem_ai_events)                    │
+│  Haiku digest + OpenAI embedding + importance score     │
+└──────────────────────────┬──────────────────────────────┘
+                           │ MemoryPromotion.*()
+                           ▼
+┌─────────────────────────────────────────────────────────┐
+│  Layer 3 — Structured Artifacts                         │
+│  mem_ai_work_items  ·  mem_ai_project_facts             │
+└──────────────────────────┬──────────────────────────────┘
+                           │ User drag-drop / Planner button
+                           ▼
+┌─────────────────────────────────────────────────────────┐
+│  Layer 4 — User-Managed Tags (planner_tags)             │
+│  Features · Bugs · Tasks — owned by users               │
+└─────────────────────────────────────────────────────────┘
+```
+
+---
+
+## Layer 1 — Mirror Tables (`mem_mrr_*`)
+
+### `mem_mrr_prompts` — Raw prompt/response pairs
+
+**Trigger**: Hook script `post_prompt.sh` → `POST /memory/{project}/prompts`
+**Responsible**: Trigger (auto, no LLM)
+
+| Column | Responsible | Notes |
+|--------|-------------|-------|
+| `id` | Trigger | UUID PK |
+| `session_id` | Trigger | Groups turns in a session |
+| `source_id` | Trigger | External ID from hook |
+| `prompt` | Trigger | Raw user input |
+| `response` | Trigger | Raw AI response |
+| `tags` | Trigger | Inline JSONB: `{source, phase, feature, work-item, llm}` |
+| `created_at` | Trigger | Insert timestamp |
+
+**Relevance score**: 0/5 — raw data, no digest yet; useful only as source for Layer 2
+
+---
+
+### `mem_mrr_commits` — Raw git commits
+
+**Trigger**: Post-commit hook `post_commit.sh` → `POST /memory/{project}/commits`
+**Responsible**: Trigger (auto, no LLM initially)
+
+| Column | Responsible | Notes |
+|--------|-------------|-------|
+| `commit_hash` | Trigger | PK |
+| `commit_msg` | Trigger | Git commit message |
+| `summary` | **LLM** (back-propagated) | Haiku digest back-written by `process_commit()` |
+| `tags` | Trigger + LLM | Initial: `{source, phase, feature}`; LLM adds `files`, `languages`, `symbols` |
+| `session_id` | Trigger | Links to session |
+| `committed_at` | Trigger | Git timestamp |
+
+**`tags["files"]`**: `{filename: rows_changed}` — populated by `smart_chunk_diff()` from actual diff
+**`tags["symbols"]`**: class/function names from diff (Python/JS/TS) — populated by code symbol extraction
+**`tags["languages"]`**: list of languages in diff — populated by `_detect_language()`
+
+**Relevance score**: 3/5 — commit message is useful; summary + files/symbols make it 4/5
+
+---
+
+### `mem_mrr_items` — Documents, requirements, decisions
+
+**Trigger**: Manual `POST /memory/{project}/items` or CLI import
+**Responsible**: User (creates) + LLM (digests)
+
+| Column | Responsible | Notes |
+|--------|-------------|-------|
+| `id` | Trigger | UUID PK |
+| `item_type` | User | `requirement`, `decision`, `meeting`, `note` |
+| `title` | User | Short title |
+| `raw_text` | User | Full document content |
+| `summary` | **LLM** | Haiku digest (back-propagated if short item) |
+| `tags` | User | Inline JSONB classification |
+
+**Relevance score**: 4/5 — decisions and requirements are high-value; meeting notes 3/5
+
+---
+
+### `mem_mrr_messages` — Platform messages (Slack, Teams)
+
+**Trigger**: Integration hook → `POST /memory/{project}/messages`
+**Responsible**: Trigger (auto)
+
+| Column | Responsible | Notes |
+|--------|-------------|-------|
+| `id` | Trigger | UUID PK |
+| `platform` | Trigger | `slack`, `teams`, `discord` |
+| `channel` | Trigger | Channel/thread name |
+| `messages` | Trigger | JSONB array of `{user, text, ts}` |
+| `tags` | Trigger | Session/feature classification |
+
+**Relevance score**: 2/5 — discussion context; useful when linked to features
+
+---
+
+## Layer 2 — AI Events (`mem_ai_events`)
+
+**Trigger**: `MemoryEmbedding.process_*()` — called after each mirror INSERT
+**Responsible**: LLM (digest + importance) + Trigger (embedding)
+
+| Column | Responsible | Notes |
+|--------|-------------|-------|
+| `id` | Trigger | UUID PK |
+| `event_type` | Trigger | `prompt_batch`, `commit`, `item`, `message`, `session_summary`, `workflow` |
+| `source_id` | Trigger | FK to mirror row |
+| `session_id` | Trigger | Propagated from mirror |
+| `chunk` | Trigger | 0=summary/digest, 1+=detail chunks |
+| `chunk_type` | Trigger | `full`, `summary`, `section`, `diff_file`, `class`, `function` |
+| `content` | **LLM** | Haiku digest text (chunk=0); raw diff/code (chunk>0) |
+| `summary` | **LLM** | Haiku 1-2 sentence summary |
+| `action_items` | **LLM** | Extracted ope

### `commit` — 2026-04-07

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index bc83c5d..4b14c9f 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -215,7 +215,8 @@ class MemoryTagging:
     async def match_work_item_to_tags(self, project: str, work_item_id: str) -> list[dict]:
         """3-level matching: exact name → semantic (>0.85 auto) → Claude judgment (0.70–0.85).
 
-        Returns list of dicts: {tag_id, relation, confidence}
+        Returns list of dicts: {tag_id, relation, confidence}.
+        Best match is auto-persisted to mem_ai_work_items.ai_tag_id.
         """
         wi = self._load_work_item(work_item_id)
         if not wi:
@@ -224,7 +225,9 @@ class MemoryTagging:
         # Level 1 — exact name match
         tag = self._find_exact_tag(project, wi['name'])
         if tag:
-            return [{'tag_id': tag['id'], 'relation': 'exact', 'confidence': 1.0}]
+            result = [{'tag_id': tag['id'], 'relation': 'exact', 'confidence': 1.0}]
+            self._persist_ai_tag_id(work_item_id, tag['id'])
+            return result
 
         # Level 2 — semantic similarity
         query = ' '.join(filter(None, [wi.get('name', ''), wi.get('description', ''), wi.get('summary', '')]))
@@ -254,8 +257,26 @@ class MemoryTagging:
             except Exception:
                 pass
 
+        # Persist best match to ai_tag_id (highest confidence)
+        if results:
+            best = max(results, key=lambda r: r.get('confidence', 0))
+            self._persist_ai_tag_id(work_item_id, best['tag_id'])
+
         return results
 
+    def _persist_ai_tag_id(self, work_item_id: str, tag_id: str) -> None:
+        """Update ai_tag_id on the work item (AI suggestion only — never overwrites tag_id)."""
+        try:
+            with db.conn() as conn:
+                with conn.cursor() as cur:
+                    cur.execute(
+                        "UPDATE mem_ai_work_items SET ai_tag_id=%s::uuid, updated_at=NOW() "
+                        "WHERE id=%s::uuid AND ai_tag_id IS DISTINCT FROM %s::uuid",
+                        (tag_id, work_item_id, tag_id),
+                    )
+        except Exception as e:
+            log.debug(f"_persist_ai_tag_id error: {e}")
+
     # ── Private helpers ─────────────────────────────────────────────────────
 
     def _load_work_item(self, work_item_id: str) -> dict | None:


## AI Synthesis

**[2026-04-07]** `schema_audit` — Removed deprecated `diff_summary` and `source_session_id` columns from work_items schema; memory_planner.py refactored to use tags['files'] dictionary structure instead. **[2026-04-07]** `performance_investigation` — Railway backend functional but slow on initial load (~60s round-trip, 0.9s per query); _SQL_UNLINKED_WORK_ITEMS and merged_into/start_date column alignment identified as bottlenecks. **[2026-04-07]** `ui_refinement` — Drag-and-drop work item behavior refined with proper hover state propagation; fixed _plannerSelectAiSubtype undefined error by ensuring planner helper functions are properly scoped to global scope. **[2026-04-07]** `memory_system` — /memory endpoint data population in progress; mem_ai_* mirror tables (events, project_facts) require trigger architecture investigation and LLM prompt synthesis flow documentation. **[2026-04-07]** `feature_launch` — shared-memory feature documented and moved to active phase with acceptance criteria; identified need for detailed API specification and concurrent access testing. **[2026-03-14]** `core_architecture` — Unified mem_ai_* table schema consolidation completed with event_id linkage for traceability; dual-layer synthesis generating 5 output files (summary, tags, facts, entities, recommendations).