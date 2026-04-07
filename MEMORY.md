# Project Memory — aicli
_Generated: 2026-04-07 01:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with Electron desktop UI and CLI, using PostgreSQL+pgvector for semantic search and multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok). It provides unified project memory management via mem_ai_* tables, work item tracking with dual status (user/AI), async DAG workflow execution, and session-based tagging. Current focus is resolving work item drag-drop persistence bugs and completing dual-status UI with proper embedding strategy for cross-table semantic matching.

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
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm dev

## In Progress

- Work item drag-and-drop UI refinement: fixing hover state propagation so only target tag highlights; ensuring dropped work items persist in correct parent and disappear from source list after page reload
- Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification
- Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cosine-similarity matching with planner_tags across work_items and memory_items tables
- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state
- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
- Work item column semantics clarification: investigating source_session_id usage and resolving column alignment inconsistencies in work_items table display

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

### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/aicli/context.md b/workspace/aicli/_system/aicli/context.md
index c4643a1..a3dbb88 100644
--- a/workspace/aicli/_system/aicli/context.md
+++ b/workspace/aicli/_system/aicli/context.md
@@ -1,9 +1,9 @@
 [Project Facts] auth_pattern=login_as_first_level_hierarchy; backend_startup_race_condition_fix=retry_logic_handles_empty_project_list_on_first_load; data_model_hierarchy=clients_contain_multiple_users; data_persistence_issue=tags_disappear_on_session_switch; db_engine=SQL; db_schema_method_convention=_ensure_shared_schema_replaces_ensure_project_schema
 
 [PROJECT CONTEXT: aicli]
-aicli is a shared AI memory platform combining a Python FastAPI backend with a desktop Electron UI and CLI, using PostgreSQL+pgvector for semantic search and multiple LLM providers (Claude/OpenAI/DeepSeek/Gemini/Grok). It provides unified project memory management, work item tracking with dual-status (user/AI), async DAG workflow execution, and session-based tagging/phase management. Current focus is on resolving work item persistence bugs in tag-linking and improving UI for drag-drop interactions between panes.
+AI-powered development CLI with multi-provider support
 Stack: cli=Python 3.12 + prompt_toolkit + rich, backend=FastAPI + uvicorn + python-jose + bcrypt + psycopg2, frontend=Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server, ui_components=xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre, storage_primary=PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 In progress: Work item tag-linking persistence and display: fixed _loadTagLinkedWorkItems filter logic where ai_category was incorrectly matching work item's category instead of tag's category; work items now persist and display correctly after drag-drop linkage and page reload, Work item dual-status UI implementation: status_user dropdown for user control + status_ai badge for AI suggestions with separate color indicators; integrated into table headers and item drawer, Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cross-table cosine-similarity matching with planner_tags
 Decisions: Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files; Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features); JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
 Entities: [feature] pagination (0ev)
-Last work (2026-04-06): Looks better, still when I drag work_item - I do not see that droped under the item (now also when I try to go out and come back to the same screen) .
\ No newline at end of file
+Last work (2026-04-06): I would like to be able to move work_item back to work_item or to another items. also merge - merge can happend only to work_items, and it can make on
\ No newline at end of file


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/CONTEXT.md b/workspace/aicli/_system/CONTEXT.md
index 3edf2ee..bd3121d 100644
--- a/workspace/aicli/_system/CONTEXT.md
+++ b/workspace/aicli/_system/CONTEXT.md
@@ -1,14 +1,14 @@
 # Project Context: aicli
 
-> Auto-generated 2026-04-06 22:57 UTC — do not edit manually.
+> Auto-generated 2026-04-07 01:05 UTC — do not edit manually.
 
 ## Quick Stats
 
 - **Provider**: claude
 - **GitHub**: https://github.com/biskilled/exp1.git
 - **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
-- **Sessions**: 401
-- **Last active**: 2026-04-06T22:55:18Z
+- **Sessions**: 402
+- **Last active**: 2026-04-06T23:06:20Z
 - **Last provider**: claude
 - **Version**: 2.1.0
 


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/CLAUDE.md b/workspace/aicli/_system/CLAUDE.md
index d1e6105..926a2b9 100644
--- a/workspace/aicli/_system/CLAUDE.md
+++ b/workspace/aicli/_system/CLAUDE.md
@@ -1,30 +1,122 @@
-# Project: aicli
+# Senior Python Architect — aicli
 
-## Active Work
+You are a senior Python software architect with deep expertise in:
+- Python 3.12+ type system, pathlib, asyncio
+- CLI tool design (prompt_toolkit, rich, typer)
+- LLM provider APIs (Anthropic, OpenAI, DeepSeek, Gemini, xAI)
+- FastAPI backend design
+- YAML-based workflow systems
+- File-based persistence (JSONL, JSON, CSV) — no unnecessary databases
 
-- `#20076 embeddings` [bug] — Users cannot copy text from the history section in the UI, limiting usability for extracting conversation data.
-History 
-- `#20075 auth` [bug] — llm_source field contains invalid or inconsistent data that doesn't match expected values or schema requirements.
-Multip
-- `#20069 mcp` [bug] — History table contains numerous events that don't make sense and appear to be erroneous data. Needs cleanup of invalid e
-- `#20068 dropbox` [bug] — Users cannot copy text from the history UI, limiting usability of viewing historical prompts and responses
-- `#20065 auth` [bug] — aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b
-- `#20066 billing` [bug] — History view only shows prompts, not LLM responses. After fixes, only small text snippets are displayed instead of full 
-- `#20061 billing` [bug] — In route_history line 470, execute_values(cur, _SQL_BATCH_UPSERT, rows) throws 'ON CONFLICT DO UPDATE command cannot aff
-- `#20063 UI` [bug] — Users are unable to copy text from the history view in the UI, limiting the ability to export or reuse historical prompt
-- `#20062 mcp` [bug] — History view shows only prompts but not LLM responses, or displays only small text snippets instead of full prompt and L
-- `#20059 Spurious history events in database` [bug] — History table contains numerous nonsensical events from previous sessions that should not be there. Data integrity issue
-- `#20056 SQL execute syntax error` [bug] — Error in route_history line 470 with cur.execute(b''.join(parts)) call to execute_values(). Incomplete or malformed SQL 
-- `#20053 Copy text functionality missing from history UI` [bug] — Users cannot copy text from the history section of the UI, which limits usability for reviewing and sharing past interac
+## Your Principles
 
-## Last Session _2026-04-06 13:11_
+- **Simplicity over cleverness**: a 20-line function beats a 200-line abstraction
+- **Read before writing**: always understand existing code before modifying it
+- **Engine/workspace separation**: aicli/ is engine (code), workspace/ is content (prompts, data)
+- **Provider contract**: every provider has send(prompt, system) → str and stream() → Generator
+- **No shared state between CLI and UI backend** — they are independent services
 
-- • Reviewed the main mem_ai_work_items table structure to understand column usage and alignment • Identified that source_session_id references parent session context but usage needs clarification • Found 3 content columns (content, summary, requirements) with unclear differentiation — need to define purpose for each • Identified tags column should merge tags from mem_ai_events table • Flagged that column alignment and data flow between tables needs documentation before proceeding with changes
+## Code Quality Standards
 
-## Do Not Touch
+- All functions have type hints
+- All file paths use `Path` objects
+- No raw `print()` in library code — use `console.print()` or `logger`
+- Exception messages tell the user what to do, not just what went wrong
+- New modules get a one-paragraph docstring explaining why they exist
 
-- `pagination`
+## Key Architectural Decisions
+
+- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
+- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
+- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
+- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
+- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
+- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
+- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
+- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
+- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
+- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
+- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
+- 

### `commit` — 2026-04-07

diff --git a/workspace/_templates/memory/prompts.yaml b/workspace/_templates/memory/prompts.yaml
index 1b2110a..f9e5a6f 100644
--- a/workspace/_templates/memory/prompts.yaml
+++ b/workspace/_templates/memory/prompts.yaml
@@ -211,6 +211,22 @@
     {"score": N, "critique": "...", "improved_summary": "...", "relations": [{"from": "tag-slug", "relation": "...", "to": "tag-slug", "note": "..."}]}
     Use empty array for relations if none detected.
 
+- name: planner_summary
+  category: memory
+  description: "Generate a concise planner document for a feature/bug/task tag"
+  content: |
+    You are a technical project planner. Given a tag with linked work items and their commit
+    history, produce a concise planner document.
+
+    Return ONLY valid JSON with keys:
+    - use_case_summary: short paragraph (2-4 sentences) describing purpose and current state
+    - done_items: list of completed action items (1-2 lines each)
+    - remaining_items: list of what still needs to be done (1-2 lines each)
+    - acceptance_criteria: list of testable QA criteria (1 line each)
+    - work_item_updates: [{id, remaining_action_items, acceptance_criteria, summary (3-4 sentences)}]
+
+    Be concise. Per-work-item summary: max 3-4 sentences.
+
 - name: memory_feature_snapshot
   category: memory
   description: "Alias for feature_snapshot"


### `commit` — 2026-04-07

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 4a9a9aa..fab0a55 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -148,6 +148,28 @@ export function renderEntities(container) {
   window._plannerDrawerRemoveLink = _plannerDrawerRemoveLink;
   window._plannerGenerateSnapshot = _plannerGenerateSnapshot;
   window._plannerDrawerMerge      = _plannerDrawerMerge;
+
+  window._plannerRunPlan = async (tagId, tagName, catName, project) => {
+    const btn = document.getElementById('drawer-planner-btn');
+    const docSpan = document.getElementById('drawer-planner-doc');
+    if (btn) { btn.disabled = true; btn.textContent = '…'; }
+    try {
+      const r = await api.tags.plan(tagId, project);
+      toast(`Planner done · ${r.work_items_updated} items synced`, 'success');
+      if (docSpan) docSpan.innerHTML =
+        `<a href="#" onclick="event.preventDefault();window._plannerOpenDoc('${_esc(r.doc_path)}','${_esc(project)}')"
+           style="color:var(--accent);text-decoration:underline">&#128196; ${_esc(r.doc_path)}</a>`;
+      setTimeout(() => window._plannerOpenDrawer && window._plannerOpenDrawer(
+        getCacheCategories().find(c => c.name === catName)?.id, tagId), 300);
+    } catch (e) { toast('Planner error: ' + e.message, 'error'); }
+    finally { if (btn) { btn.disabled = false; btn.textContent = '&#9641; Run Planner'; } }
+  };
+
+  window._plannerOpenDoc = (docPath, project) => {
+    const nav = document.querySelector('[data-view="documents"]');
+    if (nav) nav.click();
+    setTimeout(() => window._documentsOpenFile?.(docPath, project), 250);
+  };
   window._plannerOpenWorkItemDrawer = (id, cat, proj) => _openWorkItemDrawer(id, cat, proj, null, '#4a90e2', '📋');
   window._wiBotDragStart = (e, id, name, cat) => {
     _dragWiData = { id, ai_name: name, ai_category: cat };
@@ -846,6 +868,27 @@ async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon
           </div>
         </div>
 
+        <!-- Stats row -->
+        <div style="display:flex;gap:0.6rem;flex-wrap:wrap;font-size:0.6rem;color:var(--muted)">
+          <span>&#128172; <span id="wi-stat-prompts-${id}">${wi.interaction_count||0} prompts</span></span>
+          <span id="wi-stat-words-${id}">~… words</span>
+          <span>&#8859; ${wi.commit_count||0} commits</span>
+          <span id="wi-stat-files-${id}"></span>
+        </div>
+
+        <!-- Start date -->
+        <div>
+          <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
+                      letter-spacing:.06em;margin-bottom:0.2rem">Start Date</div>
+          <input type="date"
+            value="${wi.start_date ? wi.start_date.slice(0,10) : ''}"
+            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
+                   font-family:var(--font);font-size:0.65rem;padding:0.2rem 0.4rem;
+                   border-radius:var(--radius);outline:none"
+            onchange="api.workItems.patch('${id}','${project}',{start_date:this.value||''})
+                        .catch(e=>toast(e.message,'error'))" />
+        </div>
+
         <!-- Description -->
         <div>
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
@@ -1018,6 +1061,40 @@ async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon
           ${c.summary ? `<div style="color:var(--muted);font-size:0.58rem;margin-top:0.15rem">${_esc(c.summary.slice(0,80))}</div>` : ''}
           <div style="color:var(--muted);font-size:0.55rem;margin-top:0.1rem">${c.commit_hash ? c.commit_hash.slice(0,8) : ''} · ${c.committed_at ? c.committed_at.slice(0,10) : ''}</div>
         </div>`).join('');
+
+      // Parse file stats from commits
+      const allFiles = {};
+      let totalAdded = 0, totalRemoved = 0;
+      commits.forEach(c => {
+        if (!c.diff_summary) return;
+        const ins = (c.diff_summary.match(/(\d+) insertions?\(\+\)/)||[])[1];
+        const del = (c.diff_summary.match(/(\d+) deletions?\(-\)/)||[])[1];
+        if (ins) totalAdded += parseInt(ins);
+        if (del) totalRemoved += parseInt(del);
+        c.diff_summary.split('\n').forEach(line => {
+          const m = line.match(/^\s*(.+?)\s*\|\s*\d+/);
+          if (m) allFiles[m[1].trim()] = true;
+        });
+      });
+      const nFiles = Object.keys(allFiles).length;
+      const filesEl = document.getElementById(`wi-stat-files-${id}`);
+      if (filesEl && nFiles > 0)
+        filesEl.textContent = `&#128193; ${nFiles} files · +${totalAdded}/-${totalRemoved}`;
+      if (nFiles > 0) {
+        const listHtml = Object.keys(allFiles).map(f =>
+          `<div style="font-size:0.57rem;color:var(--muted)">${_esc(f)}</div>`).join('');
+        el.insertAdjacentHTML('beforeend',
+          `<details style="margin-top:4px"><summary style="font-size:0.58rem;
+             color:var(--muted);cursor:pointer">Files (${nFiles})</summary>${listHtml}</details>`);
+      }
+
+      // Load interactions for word count
+      api.workItems.interactions(id, project, 100).then(data => {
+        const total = (data?.interactions||[]).reduce(
+          (s, i) => s + (i.prompt||'').length + (i.response||'').length, 0);
+        const wordEl = document.getElementById(`wi-stat-words-${id}`);
+        if (wordEl) wordEl.textContent = `~${Math.round(total/5).toLocaleString()} words`;
+      }).catch(() => {});
     }).catch(() => {
       const el = document.getElementById(`wi-commits-${id}`);
       if (el) el.textContent = 'No linked commits';
@@ -1405,6 +1482,22 @@ function _renderDrawer() {
         </div>
       </div>` : ''}
 
+      <!-- Planner -->
+      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
+        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
+                    letter-spacing:.06em;margin-bottom:0.35rem">Planner</div>
+        <div style="display:fle

### `commit` — 2026-04-07

diff --git a/ui/frontend/utils/api.js b/ui/frontend/utils/api.js
index 2d9c802..f787c62 100644
--- a/ui/frontend/utils/api.js
+++ b/ui/frontend/utils/api.js
@@ -322,6 +322,7 @@ api.tags = {
   delete:         (id, proj, force=false) => _del(`/tags/${enc(id)}?project=${enc(proj)}${force?'&force=true':''}`),
   merge:                 (body)  => _post('/tags/merge', body),
   migrateToAiSuggestions:(proj) => _post(`/tags/migrate-to-ai-suggestions?project=${enc(proj)}`),
+  plan:           (id, proj)     => _post(`/tags/${enc(id)}/plan?project=${enc(proj)}`),
   getSources:     (id, proj)     => _get(`/tags/${enc(id)}/sources?project=${enc(proj)}`),
   addSource:      (body)         => _post('/tags/source', body),
   removeSource:   (id)           => _del(`/tags/source/${enc(id)}`),


## AI Synthesis

**[2026-04-07]** Context auto-refresh — Project now at 402 sessions, maintaining unified memory tables (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features) for cross-session knowledge. **[2026-04-06]** Work item tag-linking persistence — Fixed regression where ai_category filter was matching work item's own category instead of tag's category in _loadTagLinkedWorkItems; work items now correctly persist after drag-drop and page reload. **[2026-04-06]** Dual-status UI integration — Implemented status_user dropdown + status_ai badge with distinct color indicators throughout work item table and drawer; aligned with DB schema for user vs AI control flow. **[2026-04-06]** Work item embedding strategy — Unified space via code_summary + requirements + summary fields for cosine-similarity cross-matching with planner_tags; enables semantic work item discovery and merging. **[2026-04-06]** Hover state propagation — Identified drag-drop hover regression where non-target tags incorrectly highlighted; only target should highlight on drag-over. **[2026-04-06]** Frontend scoping fix — _plannerSelectAiSubtype and other planner helpers need proper global export to resolve undefined reference in routers.route_logs. **[2026-04-06]** Session ordering behavior — Confirmed sessions sort by created_at (not updated_at) to prevent reordering when tags/phases are applied post-session. **[2026-04-06]** Memory endpoint — /memory runs Claude Haiku dual-layer synthesis with 5 output files and LLM response summarization; auto-tags deduplicated by timestamp. **[2026-04-06]** Column semantics — source_session_id references parent session context in work_items; clarification needed on when/how it's populated vs inherited. **[2026-04-06]** Deployment confidence — Railway cloud + Electron-builder desktop fully operational; local dev via bash start_backend.sh + npm run dev.