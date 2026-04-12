# Project Memory — aicli
_Generated: 2026-04-12 18:35 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Facts

- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- **ai_tag_suggestion_ux**: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip improved from 'No existing tag' to 'Does not exist yet'
- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **date_format_frontend**: YY/MM/DD-HH:MM format in work item panel
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **event_count_column_semantics**: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
- **frontend_sticky_header_pattern**: CSS position:sticky;top:0;z-index:1 on table headers for work_items panel
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states via onmouseenter/onmouseleave, escaped string interpolation in onclick via _esc()
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **mcp_tools_count**: 12+ tools including semantic search with work_items vector search, work item management, session tagging
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_sync_workflow**: /memory endpoint executes embedding pipeline refresh to sync prompts with work_items and detect new tags
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_feature**: tags display under work_items in shared memory context
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_issue_active**: route_work_items latency ~60s; investigating _SQL_UNLINKED_WORK_ITEMS indexing and mem_ai_events join optimization
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
- **planner_tag_schema_consolidation_proposed**: drop seq_num and source columns; keep creator only; reduce descriptors (short_desc, full_desc, requirements, acceptance_criteria, summary, action_items, design) to essential fields
- **prompt_architecture**: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- **prompt_count_metric**: distinct metric tracked separately from event_count in work items API response
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **prompt_work_item_trigger_automation**: _run_promote_all_work_items() integrated into /memory command pipeline to refresh AI text fields and embedding vectors during memory generation
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:embedding_integration:prompt_work_item_trigger**: implements
- **rel:embedding_vectors:semantic_search**: enables
- **rel:event_filtering:noise_reduction**: implements
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:mcp_tool_memory:work_items_table**: depends_on
- **rel:mem_ai_events:work_items**: depends_on
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **rel:session_context:prompt_counter**: implements
- **rel:stag_command:tag_command**: replaces
- **rel:sticky_header:work_items_panel**: implements
- **rel:tag_reminder:session_context**: depends_on
- **rel:ui_notifications:error_handling**: related_to
- **rel:wiDeleteLinked:entities_js**: implements
- **rel:wiUnlink:wiRowLoading**: depends_on
- **rel:work_item_api:prompt_count**: depends_on
- **rel:work_item_consolidation:desc_ai**: depends_on
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_embedding:prompt_work_item_trigger**: implements
- **rel:work_item_panel_sort:prompt_count**: implements
- **rel:work_item_panel:state_management**: implements
- **rel:work_item_vector_search:mcp_tools**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **session_context_prompt_counter**: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_command_alias**: /stag replaces /tag due to Claude Code skill name conflict; identical functionality with immediate availability
- **tag_creation_workflow**: _wiPanelCreateTag creates tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
- **tag_filtering_scope_issue**: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **tag_reminder_display_format**: soft: '┄ Prompt #{N} ╌ still on: {tags}'; hard: multi-line box with current tags and re-send/update instructions
- **tag_reminder_feature**: soft reminder every N prompts (default 8, configurable via TAG_REMINDER_INTERVAL), hard check at 3× interval with tag confirmation requirement
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **user_tags_rendering**: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- **work_item_column_consolidation**: summary consolidated into desc_ai to reduce redundancy; ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai refactoring completed
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- **work_item_deletion_handler**: _wiDeleteLinked in entities.js with confirmation dialog and _wiRowLoading state management
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_embedding_integration**: _embed_work_item() persists vectors for name_ai + desc_ai + summary_ai concatenation; integrated into prompt_work_item() trigger and new work item creation flow
- **work_item_event_association**: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
- **work_item_panel_column_order**: Name, prompt_count, commit_count, event_count, updated_at (prompts column added before commits, events moved last)
- **work_item_panel_column_widths**: prompt_count:46px, commit_count:46px, event_count:46px (resized from 52px event_count + 52px commit_count)
- **work_item_panel_sortable_fields**: prompt_count, event_count, commit_count, seq_num (prompt_count added to sort handler)
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges
- **work_item_unlink_handler**: _wiUnlink uses _wiRowLoading(id, true) for loading state during patch operation
- **work_item_vector_search**: MCP tool_memory.py semantic search includes work_items table with embedding <=> operator, returns category/name/description/status for non-archived items

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
- **mcp**: Stdio MCP server with 12+ tools (semantic search with work_items vectors, work item management, session tagging)
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extension
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
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (m001-m019 framework)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories
- **embeddings**: text-embedding-3-small (1536-dim vectors) in mem_ai_events.embedding and mem_ai_work_items.embedding

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags_relations, project_facts, work_items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Work item column naming: name_ai, category_ai, desc_ai consolidated for consistency; embedding vectors persisted for semantic search in MCP tools
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise
- Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); permanent chip indicators without deletion
- MCP stdio server with 12+ tools including semantic search with vector embeddings on work_items table
- planner_tag table schema consolidation: removing seq_num (always null), merging source into creator field, reducing descriptor columns
- Railway cloud deployment (Dockerfile + railway.toml) + Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Work item embedding integration: _embed_work_item() persists 1536-dim vectors for name_ai + desc_ai concatenation; integrated into prompt_work_item() trigger during /memory command execution
- Work item vector search in MCP: tool_memory.py semantic search includes work_items table with embedding <=> operator, returning category/name/description/status for non-archived items
- planner_tag schema cleanup: removing seq_num column (always null, no auto-population); consolidating source + creator into single creator field with user/ai distinction; verifying status column uniqueness against work_items.status_user/status_ai
- Secondary AI tag workflow refinement: _wiSecApprove stores confirmed metadata in ai_tags.confirmed[] array; items remain visible with permanent chip indicators instead of deletion
- AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'
- planner_tag column ordering migration: repositioning project_id after client_id; adding creator (user/ai distinction), updater tracking, created_at/updated_at timestamps for audit trail

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 17507d5..8010207 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item embedding integration: _embed_work_item() function persists vectors for name_ai + desc_ai + summary_ai concatenation; integrated into prompt_work_item() trigger and new work item creation flow
-- Work item vector search in MCP: tool_memory.py semantic search now includes work_items table with embedding <=> operator, returning category/name/description/status for non-archived items
-- Work item column consolidation: completed refactoring ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai; summary consolidated into desc_ai to reduce redundancy
-- prompt_work_item() trigger automation: integrated _run_promote_all_work_items() into /memory command pipeline to refresh AI text fields and embedding vectors during memory generation
+- planner_tag table schema cleanup: identified seq_num (always null, no auto-population) for removal; consolidating source + creator into single creator field; removing redundant code_summary column; verifying status column uniqueness vs. work_items.status_user/status_ai
+- Work item embedding integration: _embed_work_item() persists vectors for name_ai + desc_ai + summary_ai concatenation; integrated into prompt_work_item() trigger during /memory command execution
+- Work item vector search in MCP: tool_memory.py semantic search includes work_items table with embedding <=> operator, returning category/name/description/status for non-archived items
 - Secondary AI tag workflow refinement: _wiSecApprove stores confirmed metadata in ai_tags.confirmed[] array; items remain visible with permanent chip indicators instead of deletion
+- prompt_work_item() trigger automation: integrated _run_promote_all_work_items() into /memory command pipeline to refresh AI text fields and embedding vectors
 - AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 600b26a..e1cd405 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -1764,7 +1764,7 @@ function _renderDrawer() {
                  color:var(--text);font-family:var(--font);font-size:0.68rem;
                  padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                  resize:vertical;box-sizing:border-box;line-height:1.5"
-          onblur="api.tags.update('${v.id}', {short_desc: this.value}).catch(e=>toast(e.message,'error'))"
+          onblur="api.tags.update('${v.id}', {description: this.value}).catch(e=>toast(e.message,'error'))"
         >${_esc(v.description || '')}</textarea>
       </div>
 


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/routers/route_tags.py b/backend/routers/route_tags.py
index a0dbadb..cbeac5c 100644
--- a/backend/routers/route_tags.py
+++ b/backend/routers/route_tags.py
@@ -68,37 +68,46 @@ async def _trigger_memory_regen(project: str, tag_name: str | None = None) -> No
 
 _SQL_LIST_TAGS = """
     SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
-           t.status, t.seq_num, t.created_at,
+           t.status, t.created_at,
            tc.name AS category_name, tc.color, tc.icon,
-           t.short_desc, t.due_date, t.priority,
-           t.source, t.creator, t.full_desc, t.requirements,
-           t.acceptance_criteria, t.is_reusable, t.summary, t.action_items,
-           t.requester, t.extra,
+           t.description, t.due_date, t.priority,
+           t.creator, t.requirements, t.acceptance_criteria,
+           t.action_items, t.summary, t.requester, t.extra,
            t.embedding IS NOT NULL AS has_embedding,
-           0 AS source_count
+           0 AS source_count,
+           t.updater, t.updated_at
     FROM planner_tags t
     LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
     WHERE t.project_id = %s
       AND t.merged_into IS NULL
     ORDER BY t.created_at
 """
+# column indices for _row_to_tag:
+#  0 id  1 name  2 category_id  3 parent_id  4 merged_into
+#  5 status  6 created_at  7 category_name  8 color  9 icon
+# 10 description  11 due_date  12 priority  13 creator
+# 14 requirements  15 acceptance_criteria  16 action_items
+# 17 summary  18 requester  19 extra  20 has_embedding
+# 21 source_count (list only)  22 updater  23 updated_at
 
 _SQL_GET_TAG = """
     SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
-           t.status, t.seq_num, t.created_at,
+           t.status, t.created_at,
            tc.name AS category_name, tc.color, tc.icon,
-           t.short_desc, t.due_date, t.priority, t.requirements, t.requester, t.extra,
-           t.source, t.creator, t.full_desc, t.acceptance_criteria,
-           t.is_reusable, t.summary, t.action_items,
-           t.embedding IS NOT NULL AS has_embedding
+           t.description, t.due_date, t.priority,
+           t.creator, t.requirements, t.acceptance_criteria,
+           t.action_items, t.summary, t.requester, t.extra,
+           t.embedding IS NOT NULL AS has_embedding,
+           t.updater, t.updated_at
     FROM planner_tags t
     LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
     WHERE t.project_id = %s AND t.id = %s::uuid
 """
+# column indices for _row_to_tag_detail: same as above without source_count (idx 21)
 
 _SQL_INSERT_TAG = """
-    INSERT INTO planner_tags (project_id, name, category_id, parent_id, status)
-    VALUES (%s, %s, %s, %s, %s)
+    INSERT INTO planner_tags (project_id, name, category_id, parent_id, status, creator)
+    VALUES (%s, %s, %s, %s, %s, %s)
     ON CONFLICT (project_id, name, category_id) DO NOTHING
     RETURNING id, name, created_at
 """
@@ -159,6 +168,7 @@ class TagCreate(BaseModel):
     category_id: Optional[int] = None
     parent_id: Optional[str] = None
     status: str = "open"
+    creator: str = "user"
 
 
 class TagUpdate(BaseModel):
@@ -167,20 +177,18 @@ class TagUpdate(BaseModel):
     parent_id: Optional[str] = None
     merged_into: Optional[str] = None
     status: Optional[str] = None
-    seq_num: Optional[int] = None
-    source: Optional[str] = None
-    creator: Optional[str] = None
-    short_desc: Optional[str] = None
-    full_desc: Optional[str] = None
+    description: Optional[str] = None
     requirements: Optional[str] = None
     acceptance_criteria: Optional[str] = None
+    action_items: Optional[str] = None
+    summary: Optional[str] = None
+    design: Optional[dict] = None
     priority: Optional[int] = None
     due_date: Optional[str] = None
     requester: Optional[str] = None
     extra: Optional[dict] = None
-    is_reusable: Optional[bool] = None
-    summary: Optional[str] = None
-    action_items: Optional[str] = None
+    creator: Optional[str] = None
+    updater: Optional[str] = None
 
 
 class TagMerge(BaseModel):
@@ -221,33 +229,13 @@ def _require_db():
 
 
 def _row_to_tag(row: tuple) -> dict:
-    # Column order matches _SQL_LIST_TAGS (26 columns + source_count = index 25):
-    #  0  id
-    #  1  name
-    #  2  category_id
-    #  3  parent_id
-    #  4  merged_into
-    #  5  status
-    #  6  seq_num
-    #  7  created_at
-    #  8  category_name
-    #  9  color
-    # 10  icon
-    # 11  short_desc
-    # 12  due_date
-    # 13  priority
-    # 14  source
-    # 15  creator
-    # 16  full_desc
-    # 17  requirements
-    # 18  acceptance_criteria
-    # 19  is_reusable
-    # 20  summary
-    # 21  action_items
-    # 22  requester
-    # 23  extra
-    # 24  has_embedding
-    # 25  source_count  (only in _SQL_LIST_TAGS)
+    # Column order matches _SQL_LIST_TAGS:
+    #  0 id  1 name  2 category_id  3 parent_id  4 merged_into
+    #  5 status  6 created_at  7 category_name  8 color  9 icon
+    # 10 description  11 due_date  12 priority  13 creator
+    # 14 requirements  15 acceptance_criteria  16 action_items
+    # 17 summary  18 requester  19 extra  20 has_embedding
+    # 21 source_count  22 updater  23 updated_at
     return {
         "id":                  str(row[0]),
         "name":                row[1],
@@ -255,57 +243,36 @@ def _row_to_tag(row: tuple) -> dict:
         "parent_id":           str(row[3]) if row[3] else None,
         "merged_into":         str(row[4]) if row[4] else None,
         "status":              row[5],
-        "seq_num":             row[6],
-        "created_at":          row[7].isoformat() if row[7] else None,
-        "category_name":       row[8],
-        "color":               row[9] or "#4a90e2",
-        "icon":                row[10] or "⬡",
-        "short_desc":          row[11] or "",
-        "due_date":            row[12].isoformat() if row[12] else None,
-        "priority":           

### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index c1755fa..ed625c3 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -37,17 +37,17 @@ _SQL_GET_TAG = """
 """
 
 _SQL_INSERT_TAG = """
-    INSERT INTO planner_tags (project_id, name, category_id, status)
-    VALUES (%s, %s, %s, 'active')
+    INSERT INTO planner_tags (project_id, name, category_id, status, creator)
+    VALUES (%s, %s, %s, 'active', 'ai')
     ON CONFLICT (project_id, name, category_id) DO NOTHING
     RETURNING id
 """
 
 _SQL_LIST_TAGS = """
     SELECT t.id, t.name, t.category_id, t.parent_id, t.merged_into,
-           t.status, t.seq_num, t.created_at,
+           t.status, t.created_at,
            tc.name AS category_name, tc.color, tc.icon,
-           t.short_desc, t.due_date, t.priority, 0 AS source_count
+           t.description, t.due_date, t.priority, 0 AS source_count
     FROM planner_tags t
     LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
     WHERE t.project_id = %s
@@ -329,7 +329,7 @@ class MemoryTagging:
         with db.conn() as conn:
             with conn.cursor() as cur:
                 cur.execute("""
-                    SELECT t.id, t.name, t.category_id, t.short_desc, tc.name AS category_name
+                    SELECT t.id, t.name, t.category_id, t.description, tc.name AS category_name
                     FROM planner_tags t
                     LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
                     WHERE t.project_id = %s AND t.status != 'archived'
@@ -340,7 +340,7 @@ class MemoryTagging:
                 """, (project_id, limit))
                 rows = cur.fetchall()
                 return [{'id': str(r[0]), 'name': r[1], 'category_id': r[2],
-                         'short_desc': r[3] or '', 'category_name': r[4] or '',
+                         'description': r[3] or '', 'category_name': r[4] or '',
                          'score': 0.0} for r in rows]
 
     def _vector_search_tags(self, project: str, embedding: list, limit: int = 15) -> list[dict]:
@@ -348,7 +348,7 @@ class MemoryTagging:
         with db.conn() as conn:
             with conn.cursor() as cur:
                 cur.execute("""
-                    SELECT id, name, category_id, short_desc,
+                    SELECT id, name, category_id, description,
                            1 - (embedding <=> %s::vector) AS score
                     FROM planner_tags
                     WHERE project_id = %s AND embedding IS NOT NULL AND status != 'archived'
@@ -356,7 +356,7 @@ class MemoryTagging:
                 """, (embedding, project_id, embedding, limit))
                 rows = cur.fetchall()
                 return [{'id': str(r[0]), 'name': r[1], 'category_id': r[2],
-                         'short_desc': r[3], 'score': float(r[4])} for r in rows]
+                         'description': r[3], 'score': float(r[4])} for r in rows]
 
     async def _embed_text(self, text: str) -> list:
         """Embed text using OpenAI text-embedding-3-small."""
@@ -374,7 +374,7 @@ class MemoryTagging:
         Primary is ALWAYS populated — either an existing match or a suggested new tag name.
         """
         cand_text = '\n'.join(
-            f"- [{c.get('category_name','?')}] {c['name']} | {c.get('short_desc','')}"
+            f"- [{c.get('category_name','?')}] {c['name']} | {c.get('description','')}"
             for c in candidates
         )
         prompt = (


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index 76af7a3..6c3738f 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -106,8 +106,8 @@ _SQL_UPDATE_TAG_SNAPSHOT = """
         summary      = %s,
         action_items = %s,
         design       = %s,
-        code_summary = %s,
         embedding    = %s,
+        updater      = 'ai',
         updated_at   = NOW()
     WHERE id = %s AND project_id = %s
 """
@@ -551,7 +551,6 @@ class MemoryPromotion:
 
         ai_relations: list[dict] = parsed.pop("relations", []) or []
         design = parsed.get("design", {})
-        code_summary = parsed.get("code_summary", {})
         requirements = parsed.get("requirements", "")
         action_items = parsed.get("action_items", "")
 
@@ -566,7 +565,6 @@ class MemoryPromotion:
                         requirements,
                         action_items,
                         json.dumps(design),
-                        json.dumps(code_summary),
                         embedding,
                         tag_id,
                         project_id,


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/memory/memory_planner.py b/backend/memory/memory_planner.py
index 3471504..ab3ec1e 100644
--- a/backend/memory/memory_planner.py
+++ b/backend/memory/memory_planner.py
@@ -60,7 +60,8 @@ _SQL_GET_WI_INTERACTION_STATS = """
 
 _SQL_UPDATE_TAG = """
     UPDATE planner_tags
-    SET summary = %s, action_items = %s, acceptance_criteria = %s, updated_at = NOW()
+    SET summary = %s, action_items = %s, acceptance_criteria = %s,
+        updater = 'ai', updated_at = NOW()
     WHERE id = %s::uuid AND project_id = %s
 """
 

