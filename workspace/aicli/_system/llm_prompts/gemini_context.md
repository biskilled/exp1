# Project Context: aicli
# Generated: 2026-04-12 11:10 UTC

## Project Facts

### General

- ai_event_filtering_logic: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- ai_tag_color_default: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- ai_tag_label_format: category:name when both present, falls back to name-only, empty string if neither
- ai_tag_suggestion_debugging_status: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
- ai_tag_suggestion_feature: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- ai_tag_suggestion_ux: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip improved from 'No existing tag' to 'Does not exist yet'
- auth_pattern: login_as_first_level_hierarchy
- backend_startup_race_condition_fix: retry_logic_handles_empty_project_list_on_first_load
- code_extraction_configuration: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- commit_processing_flag: exec_llm boolean column replaces tags->>'llm' NULL check
- commit_tracking_schema: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- data_model_hierarchy: clients_contain_multiple_users
- data_persistence_issue: tags_disappear_on_session_switch
- date_format_frontend: YY/MM/DD-HH:MM format in work item panel
- db_engine: PostgreSQL with SQL parameter binding
- db_schema_management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- db_schema_method_convention: _ensure_shared_schema_replaces_ensure_project_schema
- deployment_target: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- email_verification_integration: incremental_enhancement_to_existing_signin_register_forms
- event_count_column_semantics: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
- frontend_sticky_header_pattern: CSS position:sticky;top:0;z-index:1 on table headers for work_items panel
- frontend_ui_pattern: inline event handlers with event.stopPropagation(), CSS opacity/color hover states via onmouseenter/onmouseleave, escaped string interpolation in onclick via _esc()
- known_bug_active: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- mcp_integration: embedding_and_data_retrieval_for_work_item_management
- memory_endpoint_template_variable_scoping: code_dir_variable_fixed_at_line_1120
- memory_management_pattern: load_once_on_access_update_on_save
- memory_sync_workflow: /memory endpoint executes embedding pipeline refresh to sync prompts with work_items and detect new tags
- memory_system_update_status: updated_with_latest_context_and_session_tags
- pending_feature: tags display under work_items in shared memory context
- pending_implementation: memory_items_and_project_facts_table_population
- pending_issues: project_visibility_bug_active_project_not_displaying
- performance_issue_active: route_work_items latency ~60s; investigating _SQL_UNLINKED_WORK_ITEMS indexing and mem_ai_events join optimization
- performance_optimization: redundant_SQL_calls_eliminated
- pipeline/auth: Acceptance criteria:
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
- prompt_architecture: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- prompt_count_metric: distinct metric tracked separately from event_count in work items API response
- prompt_loading_pattern: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- rel:ai_tag_suggestion:user_tags: replaces
- rel:ai_tag_suggestion:work_items_table: related_to
- rel:commit_processing:exec_llm_flag: replaces
- rel:event_filtering:noise_reduction: implements
- rel:frontend_ui_pattern:ai_tag_suggestion_feature: implements
- rel:mem_ai_events:work_items: depends_on
- rel:memory_endpoint:tag_detection: implements
- rel:memory_system:session_tags: implements
- rel:prompt_loader:mng_system_roles: replaces
- rel:route_memory:prompt_loader: depends_on
- rel:route_memory:sql_parameter_binding: depends_on
- rel:route_prompts:memory_embedding: depends_on
- rel:route_search:memory_embedding: depends_on
- rel:route_snapshots:prompt_loader: depends_on
- rel:route_work_items:sql_parameter_binding: depends_on
- rel:session_context:prompt_counter: implements
- rel:stag_command:tag_command: replaces
- rel:sticky_header:work_items_panel: implements
- rel:tag_reminder:session_context: depends_on
- rel:ui_notifications:error_handling: related_to
- rel:wiDeleteLinked:entities_js: implements
- rel:wiUnlink:wiRowLoading: depends_on
- rel:work_item_api:prompt_count: depends_on
- rel:work_item_deletion:api_endpoint: depends_on
- rel:work_item_panel_sort:prompt_count: implements
- rel:work_item_panel:state_management: implements
- route_work_items_sql_errors: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- session_context_prompt_counter: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- sql_performance_strategy: redundant_calls_eliminated_load_once_pattern
- stale_code_removed: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- tag_command_alias: /stag replaces /tag due to Claude Code skill name conflict; identical functionality with immediate availability
- tag_creation_workflow: _wiPanelCreateTag creates tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
- tag_filtering_scope_issue: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- tagging_system: nested_hierarchy_beyond_2_levels
- tagging_system_hierarchy: nested_hierarchy_beyond_2_levels_approved
- tag_reminder_display_format: soft: '┄ Prompt #{N} ╌ still on: {tags}'; hard: multi-line box with current tags and re-send/update instructions
- tag_reminder_feature: soft reminder every N prompts (default 8, configurable via TAG_REMINDER_INTERVAL), hard check at 3× interval with tag confirmation requirement
- ui_action_menu_pattern: 3_dot_menu_for_action_visibility
- ui_library: 3_dot_menu_pattern
- ui_toast_notification: toast() function displays error messages with 'error' severity level
- unimplemented_features: memory_items_and_project_facts_tables_not_updating
- unresolved_issues: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- user_tags_rendering: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- work_item_deletion_endpoint: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- work_item_deletion_handler: _wiDeleteLinked in entities.js with confirmation dialog and _wiRowLoading state management
- work_item_deletion_pattern: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- work_item_description_processing: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- work_item_display_fields: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- work_item_event_association: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
- work_item_panel_column_order: Name, prompt_count, commit_count, event_count, updated_at (prompts column added before commits, events moved last)
- work_item_panel_column_widths: prompt_count:46px, commit_count:46px, event_count:46px (resized from 52px event_count + 52px commit_count)
- work_item_panel_sortable_fields: prompt_count, event_count, commit_count, seq_num (prompt_count added to sort handler)
- work_item_panel_state_management: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- work_item_ui_column_widths: 56px–80px for multi-column sortable table headers
- work_item_ui_pattern: multi-column sortable table with proper header styling, status color badges
- work_item_unlink_handler: _wiUnlink uses _wiRowLoading(id, true) for loading state during patch operation

## Active Work Items

### #20499 history-ui-testing
Category: task
Comprehensive testing suite for the new history navigation system and enhanced UI components to ensure proper functional

### #20498 history-router-navigation
Category: feature
History router feature enables seamless navigation between chat history views with enhanced UI components for displaying

### #20497 validate-system-config-changes
Category: task
Review and validate system configuration file updates to ensure alignment with the codebase and prevent inconsistencies.

### #20496 review-chat-view-component
Category: task
Review and validate chat view component improvements across devices and scenarios to ensure proper rendering and system 

### #20495 ui-components-styling-audit
Category: task
Comprehensive audit of UI component styling and interaction patterns to ensure consistency, responsiveness, and accessib

### #20494 entities-view-feature
Category: feature
New entities view feature enabling users to display, create, edit, and delete project entities through a unified, styled

### #20493 history-export-download
Category: feature
Feature that lets users download their historical data in CSV, JSON, and PDF formats for external analysis and archival.

### #20492 history-filter-controls
Category: feature
Add interactive filter UI controls to the history view allowing users to filter by status, date, category, and other cri

### #20491 history-search-capability
Category: feature
Implement search functionality for historical data with keyword, date, and metadata filtering to improve data retrieval 

### #20490 history-display-ux-review
Category: task
Review and validate the conversation history display UI for clarity, performance with large conversation sets, and acces

### #20489 session-persistence-verification
Category: feature
Verification that session management correctly persists conversation state across browser refreshes and tab closures, en

### #20488 integrate-api-with-ui
Category: task
Integration of new CRUD APIs for entity/project management into the chat UI, enabling users to create, read, update, and

### #20487 chat-ui-message-rendering
Category: feature
Enhanced message rendering in the chat UI with improved visual presentation and interaction patterns. This work improves

### #20486 entity-project-crud-apis
Category: feature
Build complete CRUD APIs for entities and projects to support full lifecycle management in the backend. This is foundati

### #20485 embedding-model-optimization
Category: task
Fine-tune and optimize the embedding model to deliver fast, accurate vectorization for semantic search. This ensures doc

### #20484 semantic-search-integration
Category: feature
Implement semantic search using embedding models to enable meaning-based document retrieval instead of keyword matching,

### #20483 database-schema-migration
Category: task
Database schema migration to support new data structures. Critical for upcoming features and ensuring data integrity acr

### #20482 history-ui-improvements
Category: feature
Enhance the history UI to improve discoverability and usability of historical data across platforms. Focuses on clarity,

### #20481 enhanced-entities-router
Category: feature
Enhanced routing logic for entity navigation to improve data flow and user experience. This update ensures reliable navi

### #20480 update-workflow-access-patterns
Category: task
Refactor all workflow data access patterns to use the new filesystem-based storage API instead of legacy methods. This e

### #20479 validate-filesystem-storage-performance
Category: task
Validate that the migrated filesystem-based workflow storage meets performance and scalability targets. This ensures the

### #20478 migrate-workflow-storage-db-to-filesystem
Category: task
Migrate workflow data storage from database to filesystem to improve performance and scalability. This enables direct fi

### #20477 remove-unused-database-api-code
Category: task
Remove unused database and API code throughout the codebase to reduce technical debt and improve maintainability. This c

### #20476 expanded-router-endpoints
Category: feature
Enhance the projects router with new endpoints and improved route handling to support comprehensive project management o

### #20475 expand-projects-router
Category: feature
Expand the projects router with new endpoints and improved route handling to support comprehensive project management op

### #20474 log-session-stop-hook
Category: feature
A new hook template that enables custom logging behavior when sessions end, providing standardized integration points fo

### #20473 ai-assistant-config
Category: feature
Implement customizable AI assistant configuration options to enable per-project behavior customization. This allows team

### #20472 project-routing-logic
Category: feature
Enhanced project routing logic to provide better control over application navigation and behavior. This improves how the

### #20471 react-hooks-management
Category: feature
Enhance React hooks management to improve functionality and streamline development workflows. This work consolidates imp

### #20470 projects-router
Category: feature
New projects router implementation for handling project-related routing endpoints with updated system documentation.

### #20469 history-view-layout-refactor
Category: feature
Refactor the history view layout to improve organization and user experience. This enhances usability by restructuring h

### #20468 entities-router
Category: feature
A new router module that consolidates entity-related routes, improving code organization and separation of concerns with

### #20467 history-ui-layout-improvements
Category: feature
Enhance the history UI layout to improve usability and user experience when viewing historical records. This addresses n

### #20466 history-ui-filtering
Category: feature
Add filtering capabilities to the history UI enabling users to search and browse historical records efficiently. This im

### #20465 cleanup-artifact-files
Category: task
Remove temporary build and runtime artifact files (system state, session data) from the aicli codebase to reduce clutter

### #20464 database-query-handling
Category: feature
Improve the database layer's query handling logic and error management to increase reliability and debugging capability.

### #20463 restful-crud-endpoints
Category: feature
Implemented complete RESTful CRUD endpoints for entity management with full create, read, update, delete operations.

### #20462 test-work-item-movement-across-confirmations
Category: task
Comprehensive test suite validating that work items can be properly moved and linked across all three confirmation workf

### #20461 verify-tag-confirmation-workflows
Category: task
Comprehensive testing of tag confirmation UI workflows across three scenarios: confirming existing tags, creating new ta

### #20460 restart-claude-code-for-stag-skill
Category: task
Restart Claude Code IDE to activate the /stag skill alias, a workaround for /tag being a reserved command in the system.

### #20459 refactor-chat-view-component
Category: task
Refactor chat.js view component to reduce code complexity and improve maintainability. This work consolidates duplicated

### #20458 history-ui-entity-context
Category: feature
Enhance the history UI to display entity information alongside chat messages, giving users better context about referenc

### #20457 chat-view-state-management
Category: feature
Updated chat view interface to better handle state transitions and improve user interactions when switching between proj

### #20456 improved-routing-logic
Category: feature
Enhanced project routing system to streamline navigation flow and state transitions across the application. Improves use

### #20455 UI
Category: feature
Enhance the chat UI with improved visual layout and user interaction patterns to provide a better messaging experience.

### #20454 development
Category: feature
Improve the history view UI with enhanced display patterns and interaction capabilities. This work item addresses user e

### #20453 entity-routing
Category: feature
Entity routing system that enables navigation to specific entities with improved display patterns in history and chat UI

### #20452 development
Category: task
Enhance the git router to streamline version control operations and improve git-related functionality integration across

### #20451 development
Category: task
Update system state handling mechanisms to align with current best practices and improve code clarity.

### #20450 development
Category: task
Refactor the database core logic to eliminate unnecessary complexity and improve code maintainability. This simplifies c

### #20449 development
Category: task
Remove outdated router code and implementation from the project codebase.

### #20448 ai-tag-approval-workflow
Category: task
Review and document user ability to approve or remove AI-generated tags on work items to ensure proper permission contro

### #20447 session-context-historical-commits
Category: feature
Consider adding session context to historical commit backfill process to enable future code generation and improve trace

### #20446 architecture-decision
Category: task
Document the expected zero-prompt pattern for historical commits processed via backfill without active CLI sessions, ver

### #20445 work-item-commit-linking
Category: bug
Fixed SQL join from event_id to commit_short_hash via source_id to properly link work items to commits. Verify all work 

### #20444 development
Category: feature
Add extended functionality to prompts feature including UI enhancements and database layer improvements for managing add

### #20443 workflow-api-layer-update
Category: feature
Updated API layer to support new workflow features and data structures for enhanced graph workflow capabilities.

### #20442 graph-workflow
Category: feature
Improved navigation and visual components in the graph workflow interface for better usability and clarity.

### #20441 entity-views-upgrade
Category: feature
Upgraded entity views to improve overall user experience and system usability.

### #20440 graph-runner-improvements
Category: feature
Enhanced graph runner functionality for better performance and reliability.

### #20439 work-items-management-enhancements
Category: feature
Improved work items management functionality to enhance system capabilities and user experience.

### #20438 workflow-graph-frontend-visualization
Category: feature
Enhanced frontend view with improved visualization and interaction capabilities for workflow graphs, providing better UX

### #20437 graph-workflow-backend-router
Category: feature
Implemented new backend router to handle API endpoints for graph operations, enabling server-side support for workflow g

### #20436 backend-routing-graph-operations
Category: task
Updated backend routing logic to enhance support for graph-based operations and improve overall workflow architecture.

### #20435 graph-workflow-history-tracking
Category: feature
Implemented improved history tracking mechanism for graph workflow system to better capture and manage state transitions

### #20434 system-documentation-update
Category: task
Updated system documentation to reflect backend changes and improve clarity for developers. Ensure documentation is curr

### #20433 backend-database-pipeline-optimization
Category: task
Enhanced database handling and pipeline logic to improve data processing efficiency and maintainability. Review implemen

### #20432 verify-legacy-code-removal
Category: task
Ensure all references to removed legacy storage and embeddings code are cleaned up across the codebase and tests continu

### #20431 add-sql-query-comments
Category: task
Add SQL query comments at the top of each file/class per coding standards for documentation and maintainability.

### #20430 verify-composite-indexes-deployed
Category: task
Confirm migration m020 composite indexes are live and query performance improved on planner/work_items tabs.

### #20429 activate-tag-skill-new-session
Category: task
Start a new session to load the `/tag` skill for tagging mechanism with periodic reminders.

### #20428 extended-project-routing
Category: feature
Add new endpoints and routing logic to project router for expanded API functionality and granular control over project o

### #20427 verify-system-config-updates
Category: task
Test system configuration changes to ensure they don't introduce regressions or break deployment pipelines.

### #20426 review-unused-frontend-views
Category: task
Audit and document which frontend view files were removed and verify no active features depend on them.

### #20425 update-ai-context-documentation
Category: task
Updated documentation files to improve AI assistant context handling and conversation state management.

### #20424 session-based-work-item-tracking
Category: feature
Implemented session-based change tracking for work items router and entity views to enable better modification managemen

### #20423 test-context-preservation
Category: task
Test that context is properly preserved and accessible in subsequent sessions.

### #20422 validate-session-state-tracking
Category: task
Ensure session state management maintains consistency across multiple CLI invocations.

### #20421 review-context-file-updates
Category: task
Verify AI context files are properly updated and persisted after CLI session execution.

### #20420 document-env-setup
Category: task
Document the development environment setup changes to ensure team consistency and reproducibility.

### #20419 review-config-changes
Category: task
Review and validate system configuration updates to build scripts and dependencies applied during Claude CLI session.

### #20418 update-system-state-config
Category: task
Update system state and memory configurations based on learnings from Claude session fa5883c1. Review and integrate any 

### #20417 standardize-session-state-files
Category: task
Update session state file formats and structures to align with current operational standards.

### #20416 improve-memory-management
Category: task
Optimize memory management implementation across system components for better resource efficiency.

### #20415 update-ai-configuration-rules
Category: task
Review and update AI configuration rules to reflect current operational standards and ensure system consistency.

### #20414 codebase-maintenance-update
Category: task
Large-scale maintenance commit updating 34 files across the codebase. Review dependencies, configurations, and related c

### #20413 migrate-system-files-to-claude-directory
Category: task
Removed legacy flat _system files and reorganized into structured claude/ directory for improved maintainability and fil

### #20412 cleanup-stale-system-files
Category: task
Removed auto-generated system context and CLAUDE.md files from repository to reduce clutter and improve maintainability.

### #20411 dependency-and-config-updates
Category: task
Updated 33 files across codebase for maintenance and dependency alignment. Review changes to ensure compatibility and st

### #20410 validate-knowledge-base-organization
Category: task
Audit knowledge base structure to ensure organization aligns with updated configuration and supports efficient retrieval

### #20407 project-api-routes
Category: feature
Implemented new project-related API endpoints to handle project operations and data management.

### #20402 add-event-counter-field
Category: feature
Add an event counter field to the work_item display to show how many events are associated with each work item.

### #20401 propagate-tags-to-linked-events
Category: feature
Add logic to propagate user-assigned tags to all events linked to the work_item for consistency across related items.

### #20400 replace-new-item-with-refresh-button
Category: feature
Replace the 'new work_item' UI option with a 'refresh' button to reload latest work_items and update AI tags without cre

### #20399 ai-tags-query-missing-suggested-new
Category: bug
The ui_tags query does not include or display suggested_new tags for AI(NEW) suggestions, preventing users from seeing A

### #20397 refactor-system-docs-structure
Category: task
Reorganized _system documentation from monolithic structure into modular, feature-based layout to improve maintainabilit

### #20382 verify-state-persistence
Category: task
Test and validate that workspace state correctly persists across multiple sessions without data loss or corruption.

### #20378 backend-route-refactor
Category: task
Reorganized backend route structure to improve code maintainability and streamline request handling across the applicati

### #20376 verify-session-persistence
Category: task
Test that conversation history and model state properly persist across multiple sessions after the recent state tracking

### #20375 audit-configuration-references
Category: task
Review codebase for any dependencies on removed legacy configuration files to ensure no broken imports or missing contex

### #20373 maintain-session-history-logs
Category: task
Updated session history logs to maintain accurate historical records. Review log retention and archival policies.

### #20368 verify-build-pipeline
Category: task
Run full test suite and build pipeline to validate that large-scale updates haven't introduced regressions or breaking c

### #20367 review-dependency-updates
Category: task
Review and test the 38 file updates across codebase to ensure compatibility and stability after dependency or configurat

### #20365 review-claude-session-17cd46bd-changes
Category: task
Review and validate updates to AI system files and memory from Claude session 17cd46bd to ensure configurations and patt

### #20363 routing-stability
Category: bug
Resolved routing stability problems that were affecting system consistency. Enhanced reliability of message routing and 

### #20361 refactor-database-module
Category: task
Refactored database.py for improved code organization and maintainability with structural improvements.

### #20360 update-workspace-config-docs
Category: task
Updated AI workspace configuration files and memory documentation to reflect previous session changes. Ensures configura

### #20358 refactor-core-backend-modules
Category: task
Reorganized core backend modules to improve code organization and maintainability.

### #20356 verify-background-matching-persistence
Category: task
Verify background matching is completing and persisting all suggested_new tags correctly.

### #20355 drag-drop-user-tags
Category: feature
Enable drag-and-drop functionality for USER tag assignment.

### #20354 add-table-left-padding
Category: task
Add left padding to table for improved visual spacing and layout.

### #20353 expand-updated-column
Category: feature
Expand UPDATED column width to display full datetime in yyyy-mm-dd HH:mm:ss format.

### #20352 color-coded-tag-labels
Category: feature
Implement AI(EXISTS) green, AI(NEW) red, USER blue color coding in tag labels for visual distinction.

### #20350 refactor-backend-module-structure
Category: task
Reorganized backend module dependencies and structure to improve code maintainability and system initialization patterns

### #20348 remove-database-boilerplate
Category: task
Removed unnecessary database boilerplate code from the aicli workspace to streamline the codebase and reduce redundancy.

### #20347 ai-config-standardization
Category: task
Updated AI system configuration files as part of architecture improvements. Verify all environments use updated configs 

### #20344 improve-context-management
Category: task
Enhanced AI context configuration files to better handle context tracking and memory management.

### #20341 organize-session-history
Category: task
Organized and maintained session history records to improve project memory and development continuity.

### #20339 fix-backend-routing
Category: bug
Fixed minor routing issues in the backend system to ensure correct request handling.

### #20335 documentation-update-clarity
Category: task
Updated system documentation to improve clarity and consistency across the codebase.

### #20333 entities-view-api-integration
Category: feature
Update entities view to integrate with API changes, including tag-based filtering and display capabilities.

### #20332 tag-based-routing
Category: feature
Implement tag-based routing functionality to enable dynamic navigation and filtering based on entity tags.

### #20330 document-behavior-pattern-adjustments
Category: task
Document the specific behavior pattern adjustments and lessons learned that prompted the rule updates.

### #20326 system-rules-review
Category: task
Administrative review and update of system rules configuration without user-facing changes.

### #20324 entities-ui-visualization
Category: feature
Improved entities UI with better visualization and interaction patterns. Enhances user experience for entity management 

### #20323 mcp-server-protocol-upgrade
Category: feature
Upgraded MCP server with additional capabilities and improved protocol compliance. Extends server functionality and stan

### #20321 tag-suggestion-testing
Category: task
Test tag suggestion accuracy and filtering logic to ensure AI recommendations are relevant and user tags integrate corre

### #20320 mirror-events-tag-merge
Category: bug
Verify all mirror events properly merge user tags through to work items in UI.

### #20319 user-tags-info-pills
Category: feature
Fetch and display user-created tags as informational pills on work item details.

### #20318 category-name-tag-display
Category: feature
Implement category:name format for AI tag suggestions with visual differentiation between new and existing tags.

### #20317 update-project-rules-docs
Category: task
Refresh project rules documentation based on latest session findings to ensure alignment with current practices.

### #20314 sync-system-files
Category: task
System files synchronized to persist Claude session state and memory/chat context configuration.

### #20311 review-session-6ffb562b-changes
Category: task
Review and validate system files and memory state updates from Claude session 6ffb562b to ensure conversation context an

### #20309 system-directory-restructure
Category: task
Reorganized _system directory structure for better organization and developer experience.

### #20306 refactor-database-complexity
Category: task
Refactored database.py to reduce complexity and improve maintainability of database operations.

### #20305 context-persistence-validation
Category: task
Validate that system context is properly maintained and restored after CLI session execution completes.

### #20303 review-bulk-changes-235-files
Category: task
Review and validate automated bulk changes across 235 files from AI CLI session to ensure code quality and correctness.

### #20302 verify-date-format-yy-mm-dd
Category: task
Confirm date format changed to yy/mm/dd-hh:mm displays consistently across all panels.

### #20301 filter-non-work-item-tags
Category: task
Remove non-work_item tags (Shared-memory, billing) from tag display in work_items panel.

### #20300 test-tag-approval-patch-calls
Category: task
Test tag approval/removal PATCH calls update linked status correctly in the panel.

### #20299 verify-ai-tag-suggestions-population
Category: task
Verify ai_tag_name suggestions populate correctly in work_items panel rows and display as expected.

### #20298 list-work-items-mcp-server-error
Category: bug
Debug list_work_items MCP tool returning server-side errors. Investigate tool configuration and response handling.

### #20296 system-role-routing-refactor
Category: task
Reorganized system files and refactored agent/system role routing endpoints to improve configuration management and rout

### #20295 audit-system-config-changes
Category: task
Audit system configuration file changes made during CLI session to document modifications and verify correctness.

### #20293 audit-ai-workflow-commits
Category: task
Audit the auto-commit mechanism to understand which files were changed and why, establishing clearer commit message docu

### #20292 review-automated-changes
Category: task
Review and validate the 12 files modified in the automated AI session workflow from March 19. Ensure all changes align w

### #20291 audit-auto-capture-system
Category: task
Audit the automatic change capture mechanism to verify all modifications are properly tracked and intentional.

### #20290 test-multi-file-persistence
Category: task
Test the auto-save functionality across all 19 modified files to verify data integrity and proper synchronization.

### #20289 review-auto-save-implementation
Category: task
Review and verify auto-save functionality that persists changes across multiple files during AI sessions.

### #20285 review-config-sync
Category: task
Verify that all system configuration files are properly synchronized and reflect the current operational state.

### #20283 verify-refactor-integration
Category: task
Verify that refactored backend components integrate correctly and that all routing paths function as expected post-refac

### #20282 backend-architecture-refactor
Category: task
Refactored core backend architecture and router organization to improve code structure and maintainability. Review modul

### #20281 clear-aicli-system-state
Category: task
Clean up leftover system state from previous operations after session 5b19c863 completes.

### #20280 review-session-5b19c863-state-changes
Category: task
Verify that all state changes and configuration updates from session 5b19c863 were correctly persisted to system files a

### #20277 expanded-prompt-ui-views
Category: feature
Added expanded functional UI views for prompts with improved visualization. Enables better prompt interaction and manage

### #20276 expanded-entity-ui-views
Category: feature
Implemented enhanced visualization and interaction capabilities for entity UI views. Improves user experience for entity

### #20274 sync-docs-with-session-updates
Category: task
Documentation files were updated to reflect changes to memory, rules, and context from recent Claude AI session. Verify 

### #20271 remove-stale-autogenerated-files
Category: task
Cleaned up auto-generated context and system prompt files to reduce repository clutter and improve maintainability.

### #20270 refactor-system-context
Category: task
Modified system context files to better support core application functionality and improve architectural foundation.

### #20269 improve-projects-view-ui
Category: feature
Updated projects view with improved styling and layout for better presentation and usability.

### #20268 improve-history-view-ui
Category: feature
Enhanced styling and layout for the history view component to improve user experience and visual consistency.

### #20267 workflow-ui-improvements
Category: feature
Enhanced user interface with improved visual feedback and controls for better interactive experience during workflow man

### #20266 graph-workflow-persistence
Category: feature
Implemented persistence layer with automatic saving capabilities for graph workflows. Users can now save and restore wor

### #20264 review-session-5b19c863-feedback
Category: task
Review and document learnings from session 5b19c863 to identify patterns for future improvements.

### #20260 document-best-practices
Category: task
Incorporate best practices insights into existing documentation based on session learnings.

### #20258 confirm-per-feature-docs-accessible
Category: task
Verify that all per-feature documentation is properly accessible and complete under the new CLAUDE organization structur

### #20257 verify-documentation-links
Category: task
Audit all documentation links after migration from flat _system structure to per-feature organization to ensure no broke

### #20256 update-project-structure-docs
Category: task
Revise project structure documentation to accurately reflect current implementation and organization.

### #20255 clarify-project-rules
Category: task
Revise project rules documentation to incorporate new clarifications and standards discovered during development session

### #20251 session-management-tools
Category: feature
Added persistent session management tools to support maintaining user context across multiple interactions.

### #20250 entity-router-implementation
Category: feature
Implemented entity operations routing in MCP server to manage entity-related request handling and dispatch.

### #20249 chat-router-implementation
Category: feature
Added chat message routing capability to MCP server to handle message delivery across channels or endpoints.

### #20247 validate-backend-sql-propagation
Category: task
Confirm backend restart successfully applied all SQL schema/data changes with no stale connections or caching issues.

### #20246 test-header-responsive-design
Category: task
Test header styling with improved padding and visual separation across mobile, tablet, and desktop viewports.

### #20245 verify-column-widths
Category: task
Ensure updated column widths (38px→wider) display all content properly without truncation or overflow.

### #20244 document-config-changes
Category: task
Document the changes made to AI context configuration for team reference and future maintenance.

### #20243 review-claude-session-feedback
Category: task
Review and validate feedback or changes from Claude session that prompted system state and memory configuration updates.

### #20242 review-system-context-updates
Category: task
Verify that system context changes from CLI session are properly integrated with current development state.

### #20239 session-context-archival
Category: task
Review and validate the session metadata and conversation logs that were recorded to ensure proper tracking and retrieva

### #20238 chat-router-db-integration
Category: feature
Integrated database connectivity into chat router for persistent conversation storage and retrieval. Enables efficient d

### #20235 update-system-configuration
Category: task
Updated system configuration files as part of general maintenance activities.

### #20233 simplify-state-management
Category: task
Updated system state management as part of ongoing refactoring effort to enhance code clarity and reduce technical debt.

### #20232 refactor-db-core-module
Category: task
Streamlined database core module initialization logic and removed unnecessary abstractions to improve maintainability an

### #20231 review-session-04d3b8ba-changes
Category: task
Review and validate system file and memory configuration updates applied from Claude session 04d3b8ba to ensure they ali

### #20229 update-system-state-records
Category: task
Maintain current context and conversation history by updating system state and memory records after Claude session inter

### #20226 history-expanded-view
Category: feature
Implement expanded view option in history to display complete prompt and response text together in a readable format.

### #20225 history-text-copy-functionality
Category: feature
Add ability to copy text from history UI entries for easier access and sharing of prompts and responses.

### #20223 session-stop-hooks-synchronization
Category: task
Synchronized all four session-stop hooks (response logging, session summary, memory regeneration, bug detection) across 

### #20222 history-display-llm-responses
Category: feature
Updated history display to capture both LLM responses and prompts. Configured hook-response background hook to properly 

### #20221 update-system-context-documentation
Category: task
Updated system context and memory files to reflect changes made during Claude session. Ensures documentation stays synch

### #20220 update-documentation-post-cli-session
Category: task
System context and memory documentation files were updated to reflect the current state after a CLI session. Ensure all 

### #20219 test-cli-workflows
Category: task
Execute comprehensive testing of CLI workflows to ensure work items handling operates correctly after refactoring.

### #20218 update-dependent-code-for-refactor
Category: task
Update all dependent code to align with the refactored work items handling structure.

### #20217 review-work-items-structure-compatibility
Category: task
Review refactored work items structure for compatibility with CLI improvements and identify any breaking changes.

### #20216 map-table-data-flow
Category: task
Create comprehensive documentation of column alignment and data flow patterns between mem_ai_work_items and mem_ai_event

### #20215 document-tags-merge-strategy
Category: task
Document how tags column should consolidate and merge tags from mem_ai_events table into work items.

### #20214 define-content-columns-purpose
Category: task
Define clear differentiation between content, summary, and requirements columns in mem_ai_work_items table to eliminate 

### #20213 clarify-source-session-id-usage
Category: task
Document the purpose and usage patterns of source_session_id column in mem_ai_work_items table to establish parent sessi

### #20211 verify-doc-code-alignment
Category: task
Review documentation updates against actual implementation of system context, memory, and hooks to ensure consistency is

### #20210 audit-documentation-accuracy
Category: task
Review and validate remaining system context and documentation to ensure all information is current and accurate for fut

### #20209 review-undocumented-file-changes
Category: task
Investigate the 2 modified files from the 2026-04-06 commit to understand their impact and document the changes retroact

### #20208 improve-commit-message-conventions
Category: task
Establish and enforce meaningful commit message requirements to reduce ambiguity and improve project history tracking. C

### #20207 verify-dnd-compatibility
Category: task
Verify that existing _attachWorkItemDnd logic remains compatible with new draggable row attributes and test end-to-end d

### #20206 implement-table-sorting
Category: feature
Implement sorting functionality on prompts_count, commits_count, and last_update columns with appropriate SQL ordering.

### #20205 add-work-items-table-columns
Category: feature
Add name, desc, prompts_count, commits_count, and last_update columns to work_items table with proper data aggregation f

### #20204 sync-cli-documentation
Category: task
Update documentation to reflect memory state changes and rule adjustments from Claude CLI session b9e39fae. Ensure syste

### #20199 document-temp-file-management
Category: task
Document the new approach to temporary artifact management and any manual cleanup requirements for aicli context files.

### #20196 verify-legacy-session-removal
Category: task
Ensure all references to removed legacy session files are updated in imports and tests. Validate CLI functionality remai

### #20195 sync-docs-with-session-04974a99
Category: task
Updated system context and memory documentation to reflect changes from Claude session 04974a99. Ensures documentation s

### #20194 window-plannersync-initialization
Category: task
Ensure `window._plannerSync` initialization logic is robust and handles session merging without side effects or race con

### #20193 session-data-accumulation-tracking
Category: task
Implement and verify data accumulation across merged sessions for `source_session_id`, `content`, `summary`, and `requir

### #20192 undefined-function-errors-fixed
Category: bug
Resolved undefined function errors caused by stray initialization call. The `window._plannerSync` assignment now properl

### #20191 audit-system-behavior-changes
Category: task
System behavior modifications were introduced in session 04974a99. Conduct audit to ensure changes are properly document

### #20189 update-claude-cli-documentation
Category: task
Updated system context and instruction documentation files to reflect recent changes and improvements made during intera

### #20187 remove-committed-ai-files
Category: task
Cleaned up accidentally committed temporary AI CLI system context and Claude session files from repository.

### #20186 sync-docs-with-implementation
Category: task
Documentation files have been updated to reflect current implementation details and Claude AI session insights. Ensure a

### #20185 update-system-documentation
Category: task
Updated system documentation to reflect chat router enhancements and database integration changes.

### #20183 review-rule-configuration-changes
Category: task
Rule configuration handling has been modified. Ensure all related documentation, examples, and tests align with the new 

### #20180 update-documentation
Category: task
Documentation files updated to reflect Claude AI session changes and learnings. Include memory notes and rule modificati

### #20179 sync-docs-cli-session-8b91f9d9
Category: task
Documentation updates completed to reflect implementation changes from CLI session 8b91f9d9. Verify all system context a

### #20177 review-config-updates
Category: task
Verify system configuration file changes are correct and don't introduce regressions.

### #20176 integrate-claude-session-findings
Category: task
Apply improvements and changes discovered during Claude AI interactive development session to system configuration and m

### #20174 verify-dom-scoping-behavior
Category: task
Validate that DOM selector scoping properly handles injected items and that the category filter removal doesn't introduc

### #20173 drag-drop-category-filter-fix
Category: bug
Fixed drag-and-drop filtering logic in _loadTagLinkedWorkItems that was incorrectly using tag category instead of work i

### #20172 sync-docs-with-config
Category: task
Update documentation to reflect recent system context and memory configuration changes from Claude session.

### #20165 sync-docs-with-session-context
Category: task
Documentation has been updated to reflect system context and memory state from recent Claude session. Verify all finding

### #20164 audit-render-drawer-functions
Category: task
Review other _renderDrawer functions across codebase for similar variable scope and field mapping issues.

### #20163 verify-drawer-ui-population
Category: task
Test and verify that property drawer populates correctly for all tag types in the UI after backend restart.

### #20162 restart-backend-apply-sql-update
Category: task
Restart backend service to apply the updated SQL query with newly cached fields.

### #20161 add-missing-cache-fields-sql
Category: task
Updated SQL query to include missing cached fields (requirements, acceptance_criteria, priority) for tag properties.

### #20160 tag-property-drawer-variable-scope
Category: bug
Fixed undefined catName variable and field name mismatch (short_desc vs description) in tag property drawer display logi

### #20158 sql-column-selection-route-work-items-288
Category: bug
Review and complete incomplete column selection in merged work item query at line 288 of route_work_items function.

### #20157 sql-param-binding-route-work-items-249
Category: bug
Fix missing parameter binding in cur.execute() call at line 249 for unlinked items query in route_work_items function.

### #20155 persist-configuration-changes
Category: task
Configuration changes documented and committed to ensure future reference and consistency across sessions.

### #20154 document-system-context
Category: task
Documentation files updated to capture system context and memory management insights from Claude AI session for knowledg

### #20153 audit-workspace-context-alignment
Category: task
Audit workspace context files to confirm they reflect actual implementation details and current usage patterns.

### #20151 audit-commit-logging-hook
Category: task
Review and validate the commit logging hook to ensure it's capturing the right code change metadata for the redesigned m

### #20150 redesign-delta-metrics
Category: task
Refactor row delta (+/-) metrics in `mem_ai_commits` to capture meaningful code change statistics instead of current non

### #20145 auth
Category: task
Update documentation for memory management to reflect current best practices and implementation details from recent Clau

### #20144 update-cli-documentation
Category: task
Documentation files updated to reflect system context and memory state changes from recent CLI session work.

### #20143 update-system-context-docs
Category: task
Updated system context documentation to reflect current project state and practices.

### #20141 update-system-prompts-documentation
Category: task
System prompts have been updated and documentation needs to reflect these changes for consistency.

### #20140 verify-config-and-docs
Category: task
Verify that configuration and documentation updates from automated workflow are accurate and complete.

### #20138 configuration-updates
Category: task
Review and integrate configuration changes from collaborative development session.

### #20137 sync-ui-components
Category: task
Apply interface modifications from Claude session fa708653 to UI components and system files.

### #20136 update-system-context
Category: task
System context files have been updated to reflect current configuration. Verify all operational state changes are proper

### #20134 verify-diff-summary-schema
Category: task
Validate that diff_summary field correctly captures human-readable git --stat output across all backfilled commits.

### #20133 populate-commit-file-tags
Category: task
Extract and populate tags["files"] with actual file paths modified per commit once backfill embedding pipeline completes

### #20132 complete-commit-backfill
Category: task
Finish backfilling remaining 196 commits in mem_ai_commits table with diff_summary and file path extraction via embeddin

### #20131 update-project-documentation
Category: task
Documentation has been updated to reflect current context settings, memory configuration, and AI assistant parameters fo

### #20129 update-system-prompts
Category: task
Review and update system prompts based on Claude conversation insights to improve clarity and effectiveness.

### #20125 ddl-runner-silent-failure
Category: bug
Identified silent failure in DDL runner during initial migration, likely caused by timing issues and table locks during 

### #20124 complete-mem-mrr-commits-code-schema
Category: task
Finalized `mem_mrr_commits_code` table with all 19 columns including `full_symbol` as a generated column.

### #20123 add-commit-short-hash-column
Category: task
Added `commit_short_hash` column to database schema for the `mem_mrr_commits_code` table.

### #20122 audit-root-documentation
Category: task
Review and remove outdated system documentation files (CLAUDE.md, CONTEXT.md) from project root to maintain clean reposi

### #20121 reorganize-context-structure
Category: task
Migrated legacy flat context files into feature-scoped directories to improve code organization and maintainability.

### #20119 test-ui-optimistic-removal-failure-recovery
Category: task
Confirm UI properly restores item state when optimistic removal is followed by API failure.

### #20118 monitor-query-performance-large-datasets
Category: task
Performance test work-items endpoint with large datasets to verify CTE and LEFT JOIN optimizations are effective.

### #20117 validate-ai-tag-inference
Category: task
Test AI tag inference logic when no user-provided tag exists on commits to ensure fallback behavior works correctly.

### #20116 test-event-aggregation-pipeline
Category: task
Validate end-to-end event aggregation: trigger event from 5 prompts and verify remaining commits are properly linked to 

### #20115 verify-work-item-tag-on-commits
Category: task
Ensure work-item tags are explicitly set on commits rather than auto-inferred from feature names to maintain data integr

### #20112 verify-commit-hash-column-integrity
Category: task
Validate that the new `commit_short_hash` generated column in `mem_mrr_commits_code` is correctly populated and performa

### #20110 audit-documentation-structure
Category: task
Review remaining documentation to ensure no orphaned references or duplicated content exist after legacy file removal.

### #20104 migrate-system-docs-to-subdirectories
Category: task
Reorganize legacy flat _system documentation files into structured subdirectories to improve documentation organization 

### #20103 test-initial-migration-scenarios
Category: task
Add test cases for initial database migration to catch timing issues and table lock scenarios that caused silent failure

### #20102 verify-mem-mrr-commits-code-schema
Category: task
Validate that `mem_mrr_commits_code` table with all 19 columns including new `commit_short_hash` and generated `full_sym

### #20101 fix-ddl-runner-silent-failure
Category: bug
Resolve silent failures in DDL runner during initial migration caused by timing issues and table locks. Add error handli

### #20100 query-commits-by-files-changed
Category: feature
Build query capability to search commits by specific files modified using the extracted tags['files'] data.

### #20099 validate-file-tags-extraction
Category: task
After backfill completion, verify that tags['files'] correctly captures all modified file paths for each commit.

### #20098 complete-commits-backfill
Category: task
Finish backfilling remaining 196 commits in mem_ai_commits table to extract code changes via embedding pipeline.

### #20097 consolidate-tag-merging-logic
Category: task
Review and document how tags consolidation from mem_ai_events works across merged sessions to ensure consistency.

### #20096 fix-window-planner-sync-initialization
Category: bug
Confirm that window._plannerSync initialization stray call has been fully removed and proper assignment is occurring in 

### #20095 test-content-summary-requirements-accumulation
Category: task
Validate that content, summary, and requirements fields properly accumulate across merged sessions without data loss or 

### #20094 verify-source-session-id-tracking
Category: task
Audit source_session_id field to ensure it correctly tracks which session created/last modified each work item across me

### #20093 audit-commit-hook-logging
Category: task
Verify the commit hook is correctly logging refined delta metrics and code change data after implementing the new column

### #20092 enhance-delta-metrics
Category: feature
Redesign row delta (+/-) metrics in `mem_ai_commits` to capture meaningful code change statistics beyond raw counts, mak

### #20091 remove-diff-details-column
Category: task
Remove `diff_details` column from `mem_ai_commits` table as it only stores documentation changes and doesn't capture act

### #20090 copy-text-from-history
Category: feature
Add ability to copy text from history UI entries for easier access to previous prompts and responses.

### #20089 history-view-missing-llm-response
Category: bug
History view regressed to showing only prompt text instead of both prompt and LLM response. Full response text is no lon

### #20088 document-hook-setup
Category: task
Create comprehensive documentation on hook configuration requirements and maintenance procedures for the background resp

### #20087 hook-status-monitoring
Category: feature
Implement monitoring/health checks for hook-response and session-stop hooks to proactively detect synchronization issues

### #20086 audit-hook-configurations
Category: task
Audit all four session-stop hooks (response logging, session summary, memory regeneration, bug detection) to ensure they

### #20085 verify-history-display-coverage
Category: task
Conduct end-to-end testing of history display to confirm both LLM responses and prompts are being captured and displayed

### #20084 implement-tags-merge-logic
Category: task
Design and implement logic to merge tags from mem_ai_events table into mem_ai_work_items tags column.

### #20083 document-table-relationships
Category: task
Create documentation for data flow and column alignment between mem_ai_work_items and mem_ai_events tables, including so

### #20082 clarify-content-column-purposes
Category: task
Define the distinct purposes and usage patterns for content, summary, and requirements columns in mem_ai_work_items tabl

### #20081 add-drag-drop-persistence-tests
Category: task
Add regression tests for drag-and-drop persistence when navigating away and returning to the screen to prevent future br

### #20080 review-tag-filtering-logic
Category: task
Audit other tag-related filtering operations to ensure they use work item category rather than tag category to prevent s

### #20079 drag-drop-tag-category-filter
Category: bug
Remove incorrect category filtering in `_loadTagLinkedWorkItems` that was preventing work items from being injected into

### #20078 incomplete-column-selection-merged-query-288
Category: bug
Review and complete column selection in merged work item query on line 288 of route_work_items—ensure all required colum

### #20077 sql-parameter-binding-route-work-items-249
Category: bug
Fix cur.execute() call on line 249 in route_work_items for unlinked items query—add proper parameter binding to prevent 

### #20076 embeddings
Category: bug
Users cannot copy text from the history section in the UI, limiting usability for extracting conversation data.
History 

### #20068 dropbox
Category: bug
Users cannot copy text from the history UI, limiting usability of viewing historical prompts and responses

### #20069 mcp
Category: bug
History table contains numerous events that don't make sense and appear to be erroneous data. Needs cleanup of invalid e

### #20066 billing
Category: bug
History view only shows prompts, not LLM responses. After fixes, only small text snippets are displayed instead of full 

### #20067 auth
Category: bug
Multiple events from history table don't make sense and appear to be erroneous data that should be removed

### #20065 auth
Category: bug
aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b

### #20063 UI
Category: bug
Users are unable to copy text from the history view in the UI, limiting the ability to export or reuse historical prompt

### #20061 billing
Category: bug
In route_history line 470, execute_values(cur, _SQL_BATCH_UPSERT, rows) throws 'ON CONFLICT DO UPDATE command cannot aff

### #20062 mcp
Category: bug
History view shows only prompts but not LLM responses, or displays only small text snippets instead of full prompt and L

### #20057 auth
Category: bug
History view only displays small text snippets instead of full prompts and LLM responses. Users cannot see complete conv

### #20056 SQL execute syntax error
Category: bug
Error in route_history line 470 with cur.execute(b''.join(parts)) call to execute_values(). Incomplete or malformed SQL 

### #20059 Spurious history events in database
Category: bug
History table contains numerous nonsensical events from previous sessions that should not be there. Data integrity issue

### #20060 embeddings
Category: bug
llm_source field contains invalid or inconsistent data that doesn't match expected values or schema requirements.

### #20054 Column order not applied in mem_ai_events table
Category: bug
After requesting changes to mem_ai_events table structure (llm_source to be after project column, embedding at last colu

### #20052 History UI only shows prompts, not LLM responses
Category: bug
The history display is not showing LLM responses, only prompts. Additionally, full prompt and LLM response text is trunc

### #20053 Copy text functionality missing from history UI
Category: bug
Users cannot copy text from the history section of the UI, which limits usability for reviewing and sharing past interac

### #20055 Spurious event records in history table
Category: bug
The event history table contains many events that don't make sense and appear to be leftover data from previous history 

### #20050 Column Order Not Applied in mem_ai_events
Category: bug
After requesting changes to column order (llm_source after project, embedding at end), no changes were observed in the m

### #20049 Unexpected Historical Events in Database
Category: bug
The developer observed numerous events from history in the table that don't make sense and appear to be legacy/erroneous

### #20047 UI History Display Truncation
Category: bug
Prompts and LLM responses in history are displaying as small text instead of showing the full content. Users cannot see 

### #20048 Missing Copy Functionality in UI History
Category: bug
Users are unable to copy text from the history section in the UI, indicating missing copy-to-clipboard functionality.

### #20044 Column ordering not applied to mem_ai_events table
Category: bug
Developer noted that llm_source column was supposed to be moved after project column and embedding at the end, but chang

### #20045 Inconsistent data in mem_ai_events from history
Category: bug
Developer observed many events from history in the table that don't make logical sense and questioned if they should be 

### #20046 database.py contains outdated table definitions
Category: bug
database.py is noted as being very long and containing old table definitions that are no longer in use, causing maintena

### #20043 Tag persistence issue
Category: bug
Tags attached to prompts and commits are not visible after being saved. Additionally, new tag attachments are failing si

### #20042 Undefined column 'work_item_id' in work_item query
Category: bug
psycopg2.errors.UndefinedColumn error in route_work_i: column p.work_item_id does not exist. The query references 'p.wor

### #20039 Undefined column p.work_item_id in route_work_i
Category: bug
psycopg2.errors.UndefinedColumn error - column 'p.work_item_id' does not exist. Query references this column in a WHERE 

### #20041 Tagging system not persisting data
Category: bug
Tags attached to prompts and commits are not visible after being saved. No connection between tagging system and data re

### #20040 Column ordering mismatch in mem_ai_events table
Category: bug
llm_source column was not placed after project column as requested, and embedding column was not moved to the last posit

### #20038 SQL execution error in /history/commits/sync endpoint
Category: bug
Error occurred in route_history line 441 during execute_values() call with _SQL_BATCH_UPSERT. The cur.execute(b''.join(p

### #20032 Missing llm_source column in mem_ai_events
Category: bug
The llm_source field is missing from the mem_ai_events table, which is required for proper event tracking in the memory 

### #20033 Incorrect table name in implementation
Category: bug
Table referenced as 'mng_ai_tags_relations' but should be named 'mem_ai_tags_relations'. This naming discrepancy will ca

### #20034 Unused/irrelevant columns in schema
Category: bug
Columns 'language' and 'file_path' exist in tables but developer questions their relevance and whether they are actually

### #20031 Database changes not visible
Category: bug
Developer reports inability to see changes in the database after DDL updates. The changes were supposedly applied but ar

### #20029 Incorrect table name mng_ai_tags_relations
Category: bug
Table was incorrectly named mng_ai_tags_relations when it should be named mem_ai_tags_relations. Developer explicitly id

### #20028 Unused columns in mem_ai_events table
Category: bug
Table mem_ai_events contains deprecated columns (language, file_path) that are no longer used but haven't been removed o

### #20027 Missing llm_source field in mem_ai_events table
Category: bug
Developer noted that llm_source column is missing from the mem_ai_events table where it should be present as part of the

### #20025 Incorrect table naming convention
Category: bug
Table was named 'mng_ai_tags_relations' but should be 'mem_ai_tags_relations' according to the memory structure naming c

### #20026 Schema merge incomplete
Category: bug
pr_embeddings and pr_memory_events tables were supposed to be merged into a single 'mem_ai_events' table with an event_t

### #20022 Incorrect table name: mng_ai_tags_relations
Category: bug
Developer explicitly identified that table is named 'mng_ai_tags_relations' but should be named 'mem_ai_tags_relations'.

### #20023 Tagging functionality not fully implemented
Category: bug
Developer reports uncertainty that all tagging functionality is implemented as described in previous prompts, specifical

### #20020 Incorrect table name in tagging relations
Category: bug
Developer explicitly identified that the table name should be 'mem_ai_tags_relations' but was incorrectly named 'mng_ai_

### #20019 Table merge not completed for embeddings and events
Category: bug
pr_embeddings and pr_memory_events tables were supposed to be merged into a single 'mem_ai_events' table, but this appea

### #20018 Incorrect table name in tags relations
Category: bug
Table is named 'mng_ai_tags_relations' but should be 'mem_ai_tags_relations'. Developer explicitly identified this error

### #20017 Table consolidation not completed
Category: bug
Developer references that 'pr_embeddings' and 'pr_memory_events' were supposed to be merged into a single event table ca

### #20016 Missing tagging functionality implementation
Category: bug
Developer indicates that tagging functionality is not fully implemented. Specifically, 'mng_ai_tags_relations' table/fea

### #20014 Incomplete tagging functionality implementation
Category: bug
The mng_ai_tags_relations table/functionality appears to not be fully implemented. Developer notes indicate the tagging 

### #20015 Schema merge not completed for embeddings
Category: bug
Previous design specified that pr_embeddings and pr_memory_events should be merged into a single 'mem_ai_events' table, 

### #20013 Incorrect table name reference
Category: bug
Table name mismatch: code references 'mng_ai_tags_relations' but should be 'mem_ai_tags_relations'. This naming inconsis

### #20012 Embedding table merge not completed
Category: bug
pr_embeddings and pr_memory_events were supposed to be merged into a single mem_ai_events table, but this refactoring ap

### #20011 Missing tagging relations table implementation
Category: bug
Developer reports that mng_ai_tags_relations table is not implemented. The tagging functionality appears incomplete as e

### #20010 Ambiguous embedding method behavior
Category: bug
Confusion about embedding and chunking methods - developer questions whether using 3 embedding methods creates 3 duplica

### #20009 Documentation accuracy issue
Category: bug
The aicli_memory.md documentation file does not accurately reflect actual system flows. Developer asks if it 'shows the 

### #20007 Data source confusion - JSONL vs database
Category: bug
Developer questions whether the system is loading history from pr_prompts table or from JSONL files, suggesting the appr

### #20008 Missing embeddings-to-tagging connection
Category: bug
Developer states 'I would embedding to be connected to the tagging' indicating embeddings and tagging metadata are not p

### #20006 Potential duplicate tables in schema
Category: bug
Developer mentions concerns about duplicate tables in the database (pr_events and pr_interactions), questioning whether 

### #20000 Database table naming inconsistency
Category: bug
Table name 'pr_interation' (or 'pr_interaction') was not renamed to 'pr_prompts' in the database schema, causing mismatc

### #20004 Ambiguous embedding and chunking behavior
Category: bug
Unclear whether embedding with 3 different methods creates 3 separate database rows per prompt, and whether this only oc

### #20001 Missing table rename for junction table
Category: bug
Associated junction table 'pr_interation_tags' was not renamed to 'pr_prompts_tags', creating inconsistency in the datab

### #20002 Unclear data loading source
Category: bug
System behavior unclear regarding whether it loads history from 'pr_prompts' table or from JSONL files, with developer n

### #20003 Documentation out of sync with implementation
Category: bug
File 'aicli_memory.md' does not reflect actual flows and recent changes made to the system, requiring complete rewrite a

### shared-memory
Category: task
memory

### hooks
Category: bug
hooks

### pagination
Category: feature
pagination

### dropbox
Category: feature
dropbox

### UI
Category: feature
UI

### implement-projects-tab
Category: task
Build the UI for managing features/tasks/bugs

### test-picker-feature
Category: feature
test-picker-feature

### workflow-runner
Category: feature
workflow-runner

### auth
Category: feature
auth

## Recent Session (2026-04-12 11:10)

• User requested to work on planner_tag and change the tag to feature:planner
• Session tags updated to phase: development and feature: planner
