# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items/sync` to merge approved items into use cases.

## **database-schema-refactor** · 26/03/09-04:08 [ ] (claude)
> Type: new
> Total: 47 prompts
> User tags:
> AI existing:
> AI new:

  PROMPTS P102215 [ ] [feature] [in-progress] [3] — Merged pr_embeddings and pr_memory_events into single mem_ai_events table.

  PROMPTS P102216 [ ] [feature] [in-progress] [3] — Enhanced memory tagging system with mem_ai_tags_relations and tag management.

  PROMPTS P102218 [ ] [feature] [in-progress] [3] — Implemented manual tag relations management via developer CLI commands.

  PROMPTS P102246 [ ] [feature] [in-progress] [0] — Implement tagging mechanism with user-editable tags column in work items.

  PROMPTS P102257 [ ] [feature] [in-progress] [1] — Add language tags, improve file_change data structure with file paths and row counts.

  PROMPTS P102264 [ ] [feature] [in-progress] [0] — Create mng_projects table and migrate project references from text to foreign key.

  PROMPTS P102217 [ ] [bug] [completed] [4] — Fixed table naming error: mng_ai_tags_relations corrected to mem_ai_tags_relations.

  PROMPTS P102224 [ ] [bug] [completed] [4] — Fix database DDL changes not visible in database; refactor database.py for persistence.

  PROMPTS P102248 [ ] [bug] [in-progress] [1] — Fix undefined column error (lifecycle) and optimize slow commit loading queries.

  PROMPTS P102249 [ ] [bug] [in-progress] [1] — Fix undefined column error (work_item_id) in work items route query.

  PROMPTS P102254 [ ] [bug] [in-progress] [1] — Verify column reordering in mem_ai_events table—llm_source and embedding not updated.

  PROMPTS P102139 [ ] [task] [completed] [4] — Updated /memory context files and project documentation for next steps.

  PROMPTS P102202 [ ] [task] [in-progress] [3] — Restructured database tables with mng_, cl_, pr_ naming convention.

  PROMPTS P102203 [ ] [task] [completed] [4] — Executed database migration removing 5 stale tables, consolidated to 24 tables.

  PROMPTS P102204 [ ] [task] [in-progress] [2] — Clarified table categorization: memory_items and project_facts belong in project tables.

  PROMPTS P102205 [ ] [task] [completed] [4] — Verified mng_session_tags usage and clarified project table structure.

  PROMPTS P102207 [ ] [task] [in-progress] [2] — Implemented 3-layer table structure: mng_ (general), cl_ (client), pr_ (project).

  PROMPTS P102219 [ ] [task] [completed] [4] — Rename project facts and work items tables, add features table with upsert triggers.

  PROMPTS P102220 [ ] [task] [completed] [4] — Auto-regenerate memory files (CLAUDE.md, MEMORY.md, etc.) based on project facts and work items upse

  PROMPTS P102221 [ ] [task] [completed] [4] — Provide updated aicli_memory structure and document new memory layers and tagging relationships.

  PROMPTS P102222 [ ] [task] [completed] [4] — Merge pr_session_summaries into mem_ai_events with event_type column for session summary events.

  PROMPTS P102223 [ ] [task] [completed] [4] — Add missing llm_source column to mem_ai_events and audit unused columns like language and file_path.

  PROMPTS P102225 [ ] [task] [completed] [4] — Remove unused columns from mem_ai_events; move summary_tags to mem_ai_tags linked by row ID with AI-

  PROMPTS P102226 [ ] [task] [completed] [4] — Refactor mem_mrr_* tables: remove unused columns, consolidate tags, change commit ID to integer, fix

  PROMPTS P102228 [ ] [task] [completed] [4] — Apply same refactoring (remove unused columns, fix keys) to all mem_ai_* tables.

  PROMPTS P102230 [ ] [task] [completed] [4] — Reduce database.py file size by removing old migrations and boilerplate code.

  PROMPTS P102236 [ ] [task] [in-progress] [1] — Review database files and remove obsolete tables from codebase.

  PROMPTS P102245 [ ] [task] [in-progress] [1] — Address incomplete table structure cleanup—old tables still present.

  PROMPTS P102252 [ ] [task] [in-progress] [1] — Restructure mem_ai_events table: move llm_source, consolidate tags/metadata, use JSONB.

  PROMPTS P102253 [ ] [task] [in-progress] [0] — Reorder table columns (llm_source after project, embedding at end) and clean database.py.

  PROMPTS P102255 [ ] [task] [completed] [4] — Rename mem_ai_events to old, create new table, and migrate data.

  PROMPTS P102256 [ ] [task] [in-progress] [1] — Clarify usage of doc_type, language, file_path columns and session_action_item reusability.

  PROMPTS P102258 [ ] [task] [completed] [2] — Investigate chunk and chunk_type fields; consider moving to tags dictionary.

  PROMPTS P102259 [ ] [task] [in-progress] [2] — Clean invalid historical events, verify llm_source population, update memory table.

  PROMPTS P102265 [ ] [task] [completed] [2] — Verify prompt structure after client_id fix.

  PROMPTS P102272 [ ] [task] [completed] [4] — Audit work_items columns: clarify source_session_id, content, summary, requirements usage.

  PROMPTS P102284 [ ] [task] [completed] [4] — Verify diff_summary and diff_details columns in commits table are necessary.

  PROMPTS P102285 [ ] [task] [in-progress] [3] — Investigate commit table data capture: verify hook functionality, row change counts, files tag usage

  PROMPTS P102286 [ ] [task] [in-progress] [0] — Design extraction flow for aggregating commits linked via pr_tags_map.

  PROMPTS P102287 [ ] [task] [completed] [4] — Verify database updates: confirm commit_short_hash and generated columns applied.

  PROMPTS P102293 [ ] [task] [completed] [4] — Created db_schema.sql canonical schema file with all tables, indexes, and FK constraints.

  PROMPTS P102344 [ ] [task] [completed] [4] — Implemented table migrations m035-m036 with column reordering and cleanup of old tables.

  PROMPTS P102345 [ ] [task] [completed] [3] — Analyzed importance column usage in events table.

  PROMPTS P102346 [ ] [task] [completed] [5] — Applied migration m037 to drop importance column from mem_ai_events table.

  PROMPTS P102348 [ ] [task] [completed] [5] — Applied migrations m037-m047 including column drops, reordering, and system event tracking.

  PROMPTS P102358 [ ] [task] [completed] [5] — Created migration m051 to convert user_id from string to int and add updated_at to all tables.

  PROMPTS P102359 [ ] [task] [completed] [5] — Created migration m052 to reorder all table columns with standard column ordering rules.

---

## **memory-layer-implementation** · 26/03/09-17:56 [ ] (claude)
> Type: new
> Total: 62 prompts
> User tags:
> AI existing:
> AI new: [feature:memory-layers]

  PROMPTS P102141 [ ] [feature] [in-progress] [2] — User proposes redesigning Planner from 4 tabs to single tag management interface with category hiera

  PROMPTS P102152 [ ] [feature] [completed] [4] — AI suggestions banner added to chat UI, Phase selector clarified, and session context improved.

  PROMPTS P102153 [ ] [feature] [completed] [4] — Fixed /memory suggestions to work offline, added history router, and enabled session-to-commit linki

  PROMPTS P102159 [ ] [feature] [completed] [4] — Optimized tag loading with caching, persisted tag colors, and unified tag save mechanism for commits

  PROMPTS P102161 [ ] [feature] [completed] [4] — Added prompt-to-commit linking, showing which specific prompts triggered which commits in sessions.

  PROMPTS P102165 [ ] [feature] [completed] [4] — Deduplicated 149 tags across History/Chat/Commits and added DELETE endpoints for tag removal.

  PROMPTS P102167 [ ] [feature] [completed] [4] — Linked commits to specific prompts in History/Chat view using prompt_source_id matching.

  PROMPTS P102171 [ ] [feature] [completed] [4] — Auto-save AI suggestions as tags to session with proper category, filter by phase, and remove featur

  PROMPTS P102180 [ ] [feature] [completed] [4] — Implemented `GET /entities/summary` endpoint and enhanced `/memory` command to retrieve and synthesi

  PROMPTS P102182 [ ] [feature] [in-progress] [0] — User requested adding mng table to track prompt count and notify via aicli when /memory runs.

  PROMPTS P102190 [ ] [feature] [in-progress] [3] — Designed workflow system comparing specrails and paperclip, proposed role-based architecture with ag

  PROMPTS P102192 [ ] [feature] [completed] [4] — Designed database schema for agent roles with versioning, supporting prompt editing by admins/super-

  PROMPTS P102200 [ ] [feature] [completed] [4] — Implemented nested tag hierarchy and mapped tagging to Planner, including inline child tag creation.

  PROMPTS P102232 [ ] [feature] [in-progress] [2] — User questioned lack of embeddings in project_facts and work_items, requested MCP server update for

  PROMPTS P102247 [ ] [feature] [completed] [4] — Implemented tag bidirectional linking and referencing between commits and prompts.

  PROMPTS P102252 [ ] [feature] [completed] [4] — Refactored mem_ai_events table schema to consolidate tags/metadata and use JSONB columns.

  PROMPTS P102262 [ ] [feature] [in-progress] [1] — Consolidated feature_snapshot into tags, linked work_items to events, and aligned three-layer archit

  PROMPTS P102291 [ ] [feature] [completed] [4] — Implemented prompt-to-event-to-commit linking and work item event aggregation

  PROMPTS P102296 [ ] [feature] [completed] [4] — Implemented FK-based work item to event/commit linking via migrations

  PROMPTS P102303 [ ] [feature] [completed] [4] — Implemented sticky header and AI tag suggestion approval workflow in UI

  PROMPTS P102310 [ ] [feature] [in-progress] [3] — Implemented category-aware AI tag suggestion prioritizing task/bug/feature

  PROMPTS P102312 [ ] [feature] [in-progress] [3] — Fixed AI tag suggestion visibility and added event counter to work items

  PROMPTS P102319 [ ] [feature] [completed] [4] — Addressed query performance, DIGEST column confusion, and enabled user approval for AI tags.

  PROMPTS P102326 [ ] [feature] [completed] [5] — Populated work_item tags from mirror events and enabled code_summary and AI criteria fields.

  PROMPTS P102163 [ ] [bug] [completed] [4] — Fixed hook noise filtering, corrected task-notification logging errors, added pagination and prompt-

  PROMPTS P102170 [ ] [bug] [completed] [4] — Fixed git hook to properly link last 9 commits to prompts via session_id and Phase 5 sync.

  PROMPTS P102178 [ ] [bug] [completed] [4] — Fixed session tag propagation to History/Commits: backfilled phase field and populated commit phase

  PROMPTS P102239 [ ] [bug] [completed] [4] — Fixed database column and naming errors in chat history loading routes.

  PROMPTS P102250 [ ] [bug] [completed] [4] — Restored tag attachment functionality and tag selection UI with search and creation.

  PROMPTS P102251 [ ] [bug] [completed] [3] — Fixed commit sync error in /history/commits/sync API batch upsert operation.

  PROMPTS P102282 [ ] [bug] [completed] [4] — Removed non-existent diff_summary column and fixed commit code extraction logic

  PROMPTS P102292 [ ] [bug] [completed] [4] — Fixed missing ai_tags JSONB column in mem_ai_work_items table

  PROMPTS P102294 [ ] [bug] [completed] [4] — Fixed tag drawer rendering crash and field name mismatch in UI

  PROMPTS P102314 [ ] [bug] [completed] [4] — Fixed over-extraction of internal memory sync work items by adding exclusion rules to prompt.

  PROMPTS P102315 [ ] [bug] [completed] [4] — Fixed event counter query to show only digest events and fixed UI column naming.

  PROMPTS P102320 [ ] [bug] [completed] [4] — Fixed work item-to-commit linking by correcting source_id join logic in database query.

  PROMPTS P102327 [ ] [bug] [completed] [4] — Fixed migration to correctly map ai_phase and ai_feature tags from session/commit sources.

  PROMPTS P102347 [ ] [bug] [completed] [4] — Cleaned up event tags by removing system metadata and backfilling from mirror tables

  PROMPTS P102140 [ ] [task] [in-progress] [1] — User requests AI to summarize large feature responses and improve /memory function with tagging sugg

  PROMPTS P102154 [ ] [task] [completed] [4] — Clarified MCP server usage (not directly used by Claude Code) and improved project context routing.

  PROMPTS P102160 [ ] [task] [completed] [5] — System aligned to CLAUDE.md memory layers, /memory verification run successful, and project features

  PROMPTS P102162 [ ] [task] [completed] [5] — Implemented history.jsonl rotation, verified session_tags.json usage, and performed full codebase cl

  PROMPTS P102166 [ ] [task] [completed] [4] — Verified tag logic alignment: session tags via Chat, prompt tags via History, commit tags linked to

  PROMPTS P102168 [ ] [task] [completed] [4] — Updated memory/docs for all sessions and explained MCP accessibility for new CLI/LLM sessions.

  PROMPTS P102179 [ ] [task] [completed] [4] — Optimized database schema with real columns, indexes, and improved tag/phase retrieval for MCP effic

  PROMPTS P102181 [ ] [task] [in-progress] [4] — Provided prioritized roadmap for full memory and project management lifecycle with quick wins and lo

  PROMPTS P102185 [ ] [task] [in-progress] [3] — Audited tag usage, fixed gaps in interaction_tags pipeline and session_bulk_tag function.

  PROMPTS P102186 [ ] [task] [completed] [4] — Provided comprehensive summary of 7-part system improvements including memory stack, distillation la

  PROMPTS P102206 [ ] [task] [completed] [4] — Eliminated all mng_graph_* references, refactored to use dynamic project_table() calls across 4 file

  PROMPTS P102214 [ ] [task] [in-progress] [2] — User requested review of system state before phase 2 refactor; commit made with AI context and sessi

  PROMPTS P102233 [ ] [task] [in-progress] [2] — User requested comparison of current memory config vs previous version to assess improvement in proj

  PROMPTS P102260 [ ] [task] [in-progress] [0] — Mark 'llm_source' tag as visible in UI.

  PROMPTS P102261 [ ] [task] [in-progress] [0] — Create comprehensive memory layer documentation describing all layers and data flow.

  PROMPTS P102271 [ ] [task] [in-progress] [3] — Updated memory documentation and assessed need for session memory layer in infrastructure.

  PROMPTS P102278 [ ] [task] [completed] [5] — Synced and updated all memory files with incremental data from 211 history rows.

  PROMPTS P102289 [ ] [task] [completed] [4] — Traced and documented full commit pipeline showing prompt usage locations

  PROMPTS P102295 [ ] [task] [completed] [4] — Assessed cost and completeness of mem_mrr_commits_code population

  PROMPTS P102313 [ ] [task] [completed] [4] — Located and documented all prompts for ai_tags and work_item extraction across memory system.

  PROMPTS P102321 [ ] [task] [completed] [4] — Explained why commit-sourced work items have no linked prompts and ran memory update.

  PROMPTS P102328 [ ] [task] [completed] [4] — Clarified distinction between ai_desc (extracted) and summary (generated by promotion).

  PROMPTS P102343 [ ] [task] [in-progress] [1] — Structured events table schema redesign and clarified source_id linking for multi-event items.

  PROMPTS P102352 [ ] [task] [in-progress] [0] — User asked to verify hook-log functionality after m050 migration

---

## **performance-optimization** · 26/03/10-00:52 [ ] (claude)
> Type: new
> Total: 11 prompts
> User tags:
> AI existing:
> AI new: [task:perf-optimization]

  PROMPTS P102144 [ ] [feature] [completed] [4] — Optimized database calls by caching tags in memory and implementing smart category-value dropdown wi

  PROMPTS P102201 [ ] [bug] [completed] [4] — Fixed nested work item rendering inconsistency across categories and clarified lifecycle and pipelin

  PROMPTS P102210 [ ] [bug] [completed] [4] — Fixed database schema errors, missing project loading, and removed duplicate tables.

  PROMPTS P102211 [ ] [bug] [completed] [3] — Fixed backend startup failures, memory endpoint code_dir variable error, and project selection displ

  PROMPTS P102241 [ ] [bug] [in-progress] [1] — No response provided to drag-and-drop and counter visibility issues.

  PROMPTS P102145 [ ] [task] [completed] [4] — Designed nested tags architecture with unlimited depth using parent_id and answered feasibility befo

  PROMPTS P102183 [ ] [task] [completed] [4] — Cleaned up codebase by removing hardcoded values, moving config to dedicated config file, and optimi

  PROMPTS P102184 [ ] [task] [in-progress] [0] — No response provided to restructure memory capabilities with compressed layers.

  PROMPTS P102191 [ ] [task] [completed] [4] — Explained hardcoded pipeline in work_item_pipeline.py and identified path to merge with workflow eng

  PROMPTS P102318 [ ] [task] [completed] [4] — Optimized Planner and work items loading with 5 composite database indexes and followed query docume

  PROMPTS P102319 [ ] [task] [in-progress] [2] — Addressed query performance, DIGEST column purpose, orphaned work items, and AI tag permissions.

---

## **planner-tagging-workflow** · 26/03/10-01:14 [ ] (claude)
> Type: new
> Total: 47 prompts
> User tags:
> AI existing:
> AI new: [feature:planner-workflow]

  PROMPTS P102147 [ ] [feature] [completed] [5] — Confirmed hierarchical tag support (parent_id) implemented in database and frontend cache helpers.

  PROMPTS P102158 [ ] [feature] [in-progress] [3] — Implemented tag-by-source-id endpoint to link history entries to entity tags for /memory updates.

  PROMPTS P102164 [ ] [feature] [completed] [5] — Implemented pagination (◀ [page] / total ▶) for Chat, History, and Commits tabs.

  PROMPTS P102169 [ ] [feature] [completed] [4] — Fixed MCP config for current project and created automated MCP setup for new projects with IDE suppo

  PROMPTS P102200 [ ] [feature] [in-progress] [4] — Documented tagging mechanism with nested hierarchy and planner integration plan.

  PROMPTS P102240 [ ] [feature] [in-progress] [2] — Addressed Planner issues: lifecycle tags, bug counter, drag-drop nesting, and ai_suggestion placemen

  PROMPTS P102244 [ ] [feature] [in-progress] [3] — Reorganized AI suggestions into separate section and enhanced drag-drop tag nesting.

  PROMPTS P102274 [ ] [feature] [in-progress] [2] — System documentation updated; drag-drop work item movement and panel resizing addressed.

  PROMPTS P102277 [ ] [feature] [completed] [4] — Implemented work_item move/merge functionality with tag cleanup and side panel UI.

  PROMPTS P102297 [ ] [feature] [in-progress] [2] — Added multi-column work_item table with name, desc, prompts, commits, date and sorting.

  PROMPTS P102303 [ ] [feature] [completed] [4] — Made header sticky, added AI tag suggestions with approve/remove, and prepared memory update.

  PROMPTS P102306 [ ] [feature] [completed] [4] — Implemented category:name AI tags (bug/feature/task), user tags display, and new tag suggestions wit

  PROMPTS P102310 [ ] [feature] [completed] [4] — Implemented hierarchical AI tag suggestion prioritizing task/bug/feature, then suggesting new catego

  PROMPTS P102332 [ ] [feature] [completed] [4] — Applied migration to clean planner_tags table with creator/updater fields and reordered columns.

  PROMPTS P102334 [ ] [feature] [completed] [5] — Applied m027 migration removing AI-generated columns from planner_tags table.

  PROMPTS P102335 [ ] [feature] [in-progress] [1] — Planning to add deliveries column to planner_tags with category/type taxonomy from mng_deliveries ta

  PROMPTS P102337 [ ] [feature] [in-progress] [2] — Design specification for mem_ai_feature_snapshot table with use cases and delivery types.

  PROMPTS P102338 [ ] [feature] [completed] [4] — Implemented feature_snapshot table with migration, schema, and Haiku prompt for use-case generation.

  PROMPTS P102340 [ ] [feature] [in-progress] [1] — Implementation request for dashboard tab and pipeline execution from multiple entry points.

  PROMPTS P102353 [ ] [feature] [completed] [4] — Enhanced chat history view with session sidebar, full session IDs, timestamps (YY/MM/DD-HH:MM), and

  PROMPTS P102149 [ ] [bug] [completed] [5] — Fixed port binding restart issue by implementing freePort() to kill orphan uvicorn processes.

  PROMPTS P102150 [ ] [bug] [in-progress] [3] — Added session-level tag persistence and GET endpoint to retrieve tagged entities per session.

  PROMPTS P102201 [ ] [bug] [completed] [4] — Fixed Planner inconsistency by unifying tag renderers across all categories.

  PROMPTS P102275 [ ] [bug] [in-progress] [0] — Multiple drag-drop and work item management issues identified: hover highlighting, persistence, deta

  PROMPTS P102276 [ ] [bug] [completed] [4] — Fixed work item link persistence bug in tag view by removing category filter.

  PROMPTS P102302 [ ] [bug] [completed] [4] — Completed missing delete handler for work_item rows in bottom panel.

  PROMPTS P102311 [ ] [bug] [completed] [5] — Debugged work_item ordering by fixing seq_num NULL handling and ensuring prompts/commits link to wor

  PROMPTS P102322 [ ] [bug] [completed] [4] — Fixed UI behavior for AI tag acceptance and existing tag confirmation in work item planner.

  PROMPTS P102324 [ ] [bug] [completed] [4] — Resolved tag command conflict by creating /stag alias and tagged session with development and work_i

  PROMPTS P102325 [ ] [bug] [completed] [4] — Fixed bug where adding AI tags caused work_items to disappear; metadata tags now stay in list.

  PROMPTS P102146 [ ] [task] [completed] [4] — Clarified that new tags in chat picker are created at root level; nested tags require Planner.

  PROMPTS P102166 [ ] [task] [completed] [4] — Verified tag logic alignment: session-level tags (Chat), prompt-level tags (History), commit linkage

  PROMPTS P102191 [ ] [task] [in-progress] [3] — Identified hardcoded Pipeline in work_item_pipeline.py; explained merge path with workflow engine.

  PROMPTS P102198 [ ] [task] [in-progress] [3] — Explained Claude Agent SDK capabilities and assessment of fit for multi-agent PM/Dev/Tester/Reviewer

  PROMPTS P102199 [ ] [task] [completed] [4] — Verified parent_id field added to work items for nested tag support.

  PROMPTS P102242 [ ] [task] [in-progress] [1] — System files updated after session (no specific delivery details provided).

  PROMPTS P102243 [ ] [task] [in-progress] [1] — System context and AI rules updated after session.

  PROMPTS P102316 [ ] [task] [in-progress] [3] — Explained session management, context compression, and provided architectural overview of tag tracki

  PROMPTS P102323 [ ] [task] [completed] [4] — Clarified that /tag command works in current session without needing new session.

  PROMPTS P102330 [ ] [task] [completed] [4] — Changed session tags from work_items to planner feature tag.

  PROMPTS P102331 [ ] [task] [completed] [4] — Analyzed planner_tag table schema and proposed cleanup of redundant/unused columns.

  PROMPTS P102333 [ ] [task] [completed] [3] — Planned removal of AI-generated columns from planner_tags and clarified extra column usage.

  PROMPTS P102336 [ ] [task] [completed] [4] — Session tag 'feature: feature_snapshot' set for development tracking.

  PROMPTS P102339 [ ] [task] [completed] [4] — Analyzed aicli product architecture and provided recommendations for improving flow visibility and p

  PROMPTS P102347 [ ] [task] [completed] [4] — Cleaned up event tags to show only user-managed tags, removed system metadata from 1441 events and b

  PROMPTS P102354 [ ] [task] [completed] [4] — Moved session ID display to tag bar and fixed chat loading to sync latest chats from local JSON file

  PROMPTS P102305 [ ] [bug|feature] [completed] [5] — Fixed work_item detail loading, improved tag suggestion layout, increased fonts, styled × button, an

---

## **mcp-integration-setup** · 26/03/10-03:14 [ ] (claude)
> Type: new
> Total: 24 prompts
> User tags:
> AI existing:
> AI new: [task:mcp-setup]

  PROMPTS P102193 [ ] [feature] [completed] [4] — Completed Agent Roles implementation with auto-population and UI updates

  PROMPTS P102231 [ ] [feature] [completed] [3] — Implement tag pipeline from planner merging AI and MRR data sources

  PROMPTS P102235 [ ] [feature] [in-progress] [1] — Design drag-and-drop merge feature for planner tab with parent-child support

  PROMPTS P102188 [ ] [bug] [completed] [4] — Fixed database array parsing bug and confirmed end-to-end memory pipeline working.

  PROMPTS P102317 [ ] [bug] [completed] [4] — Resolved /tag skill unknown error and explained session restart requirement.

  PROMPTS P102177 [ ] [bug] [completed] [4] — Fixed session ordering to use creation date instead of update timestamp

  PROMPTS P102269 [ ] [bug] [completed] [4] — Fixed JSONB type casting error in route_history upsert query

  PROMPTS P102270 [ ] [bug] [completed] [4] — Fixed ON CONFLICT DO UPDATE duplicate constraint error in sync_commits route

  PROMPTS P102273 [ ] [bug] [completed] [4] — Fixed ReferenceError: _plannerSelectAiSubtype and window._plannerSync undefined errors

  PROMPTS P102279 [ ] [bug] [completed] [3] — Diagnosed slow data loading in route_work_items due to 60+ second migration on Railway

  PROMPTS P102154 [ ] [task] [completed] [4] — Clarified MCP server architecture and why Claude doesn't use it directly in web sessions.

  PROMPTS P102156 [ ] [task] [completed] [4] — Confirmed session-commit connection already exists in hooks; UI display was the missing piece.

  PROMPTS P102189 [ ] [task] [completed] [4] — Configured .mcp.json for project root and clarified MCP will activate in next Claude Code session.

  PROMPTS P102209 [ ] [task] [in-progress] [0] — Request to refactor database schema removing client-specific tables — response empty.

  PROMPTS P102237 [ ] [task] [in-progress] [0] — Identified workspace folder under backend; status of usage not stated.

  PROMPTS P102238 [ ] [task] [completed] [4] — Deleted workspace folder per user request.

  PROMPTS P102227 [ ] [task] [in-progress] [0] — Test prompt after migration (no changes recorded)

  PROMPTS P102229 [ ] [task] [in-progress] [0] — Test after mem_ai cleanup (no changes recorded)

  PROMPTS P102234 [ ] [task] [completed] [2] — Fixed workspace state and memory after session update

  PROMPTS P102263 [ ] [task] [in-progress] [0] — Test prompt after fix (no changes recorded)

  PROMPTS P102266 [ ] [task] [in-progress] [0] — Final verification prompt (no changes recorded)

  PROMPTS P102288 [ ] [task] [completed] [5] — Refactored memory module naming convention and updated all 11 callers consistently

  PROMPTS P102290 [ ] [task] [completed] [4] — Explained commit-to-work-item linkage chain and how to track metrics per work item

  PROMPTS P102329 [ ] [task] [in-progress] [0] — Column naming refactor and work_item enhancement incomplete - awaiting implementation
