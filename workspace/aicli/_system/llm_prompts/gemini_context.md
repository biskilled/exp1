# Project Context: aicli
# Generated: 2026-04-07 10:17 UTC

## Project Facts

### General

- auth_pattern: login_as_first_level_hierarchy
- backend_startup_race_condition_fix: retry_logic_handles_empty_project_list_on_first_load
- data_model_hierarchy: clients_contain_multiple_users
- data_persistence_issue: tags_disappear_on_session_switch
- db_engine: SQL
- db_schema_method_convention: _ensure_shared_schema_replaces_ensure_project_schema
- deployment_target: Claude_CLI_and_LLM_platforms
- email_verification_integration: incremental_enhancement_to_existing_signin_register_forms
- mcp_integration: embedding_and_data_retrieval_for_work_item_management
- memory_endpoint_template_variable_scoping: code_dir_variable_fixed_at_line_1120
- memory_management_pattern: load_once_on_access_update_on_save
- pending_implementation: memory_items_and_project_facts_table_population
- pending_issues: project_visibility_bug_active_project_not_displaying
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
- sql_performance_strategy: redundant_calls_eliminated_load_once_pattern
- stale_code_removed: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- tagging_system: nested_hierarchy_beyond_2_levels
- tagging_system_hierarchy: nested_hierarchy_beyond_2_levels_approved
- ui_action_menu_pattern: 3_dot_menu_for_action_visibility
- ui_library: 3_dot_menu_pattern
- unimplemented_features: memory_items_and_project_facts_tables_not_updating
- unresolved_issues: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition

## Active Work Items

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

### #20067 auth
Category: bug
Multiple events from history table don't make sense and appear to be erroneous data that should be removed

### #20066 billing
Category: bug
History view only shows prompts, not LLM responses. After fixes, only small text snippets are displayed instead of full 

### #20065 auth
Category: bug
aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b

### #20061 billing
Category: bug
In route_history line 470, execute_values(cur, _SQL_BATCH_UPSERT, rows) throws 'ON CONFLICT DO UPDATE command cannot aff

### #20063 UI
Category: bug
Users are unable to copy text from the history view in the UI, limiting the ability to export or reuse historical prompt

### #20062 mcp
Category: bug
History view shows only prompts but not LLM responses, or displays only small text snippets instead of full prompt and L

### #20056 SQL execute syntax error
Category: bug
Error in route_history line 470 with cur.execute(b''.join(parts)) call to execute_values(). Incomplete or malformed SQL 

### #20059 Spurious history events in database
Category: bug
History table contains numerous nonsensical events from previous sessions that should not be there. Data integrity issue

### #20060 embeddings
Category: bug
llm_source field contains invalid or inconsistent data that doesn't match expected values or schema requirements.

### #20057 auth
Category: bug
History view only displays small text snippets instead of full prompts and LLM responses. Users cannot see complete conv

### #20053 Copy text functionality missing from history UI
Category: bug
Users cannot copy text from the history section of the UI, which limits usability for reviewing and sharing past interac

### #20055 Spurious event records in history table
Category: bug
The event history table contains many events that don't make sense and appear to be leftover data from previous history 

### #20054 Column order not applied in mem_ai_events table
Category: bug
After requesting changes to mem_ai_events table structure (llm_source to be after project column, embedding at last colu

### #20052 History UI only shows prompts, not LLM responses
Category: bug
The history display is not showing LLM responses, only prompts. Additionally, full prompt and LLM response text is trunc

### #20049 Unexpected Historical Events in Database
Category: bug
The developer observed numerous events from history in the table that don't make sense and appear to be legacy/erroneous

### #20051 database.py Contains Obsolete Table References
Category: bug
The database.py file is very long and contains references to old/deleted tables that need to be cleaned up and updated.

### #20050 Column Order Not Applied in mem_ai_events
Category: bug
After requesting changes to column order (llm_source after project, embedding at end), no changes were observed in the m

### #20048 Missing Copy Functionality in UI History
Category: bug
Users are unable to copy text from the history section in the UI, indicating missing copy-to-clipboard functionality.

### #20047 UI History Display Truncation
Category: bug
Prompts and LLM responses in history are displaying as small text instead of showing the full content. Users cannot see 

### #20046 database.py contains outdated table definitions
Category: bug
database.py is noted as being very long and containing old table definitions that are no longer in use, causing maintena

### #20045 Inconsistent data in mem_ai_events from history
Category: bug
Developer observed many events from history in the table that don't make logical sense and questioned if they should be 

### #20044 Column ordering not applied to mem_ai_events table
Category: bug
Developer noted that llm_source column was supposed to be moved after project column and embedding at the end, but chang

### #20042 Undefined column 'work_item_id' in work_item query
Category: bug
psycopg2.errors.UndefinedColumn error in route_work_i: column p.work_item_id does not exist. The query references 'p.wor

### #20043 Tag persistence issue
Category: bug
Tags attached to prompts and commits are not visible after being saved. Additionally, new tag attachments are failing si

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

### #20034 Unused/irrelevant columns in schema
Category: bug
Columns 'language' and 'file_path' exist in tables but developer questions their relevance and whether they are actually

### #20033 Incorrect table name in implementation
Category: bug
Table referenced as 'mng_ai_tags_relations' but should be named 'mem_ai_tags_relations'. This naming discrepancy will ca

### #20031 Database changes not visible
Category: bug
Developer reports inability to see changes in the database after DDL updates. The changes were supposedly applied but ar

### #20027 Missing llm_source field in mem_ai_events table
Category: bug
Developer noted that llm_source column is missing from the mem_ai_events table where it should be present as part of the

### #20030 Incomplete table merge of pr_embeddings and pr_memory_events
Category: bug
pr_embeddings and pr_memory_events tables were supposed to be merged into a single mem_ai_events table, but the migratio

### #20029 Incorrect table name mng_ai_tags_relations
Category: bug
Table was incorrectly named mng_ai_tags_relations when it should be named mem_ai_tags_relations. Developer explicitly id

### #20028 Unused columns in mem_ai_events table
Category: bug
Table mem_ai_events contains deprecated columns (language, file_path) that are no longer used but haven't been removed o

### #20026 Schema merge incomplete
Category: bug
pr_embeddings and pr_memory_events tables were supposed to be merged into a single 'mem_ai_events' table with an event_t

### #20025 Incorrect table naming convention
Category: bug
Table was named 'mng_ai_tags_relations' but should be 'mem_ai_tags_relations' according to the memory structure naming c

### #20023 Tagging functionality not fully implemented
Category: bug
Developer reports uncertainty that all tagging functionality is implemented as described in previous prompts, specifical

### #20022 Incorrect table name: mng_ai_tags_relations
Category: bug
Developer explicitly identified that table is named 'mng_ai_tags_relations' but should be named 'mem_ai_tags_relations'.

### #20024 Table merge not completed: pr_embeddings and pr_memory_events
Category: bug
Developer references that pr_embeddings and pr_memory_events were supposed to be merged into a single event table called

### #20021 Table merge not completed for embeddings and memory events
Category: bug
Developer notes that pr_embeddings and pr_memory_events were supposed to be merged into a single 'mem_ai_events' table, 

### #20020 Incorrect table name in tagging relations
Category: bug
Developer explicitly identified that the table name should be 'mem_ai_tags_relations' but was incorrectly named 'mng_ai_

### #20019 Table merge not completed for embeddings and events
Category: bug
pr_embeddings and pr_memory_events tables were supposed to be merged into a single 'mem_ai_events' table, but this appea

### #20018 Incorrect table name in tags relations
Category: bug
Table is named 'mng_ai_tags_relations' but should be 'mem_ai_tags_relations'. Developer explicitly identified this error

### #20016 Missing tagging functionality implementation
Category: bug
Developer indicates that tagging functionality is not fully implemented. Specifically, 'mng_ai_tags_relations' table/fea

### #20017 Table consolidation not completed
Category: bug
Developer references that 'pr_embeddings' and 'pr_memory_events' were supposed to be merged into a single event table ca

### #20014 Incomplete tagging functionality implementation
Category: bug
The mng_ai_tags_relations table/functionality appears to not be fully implemented. Developer notes indicate the tagging 

### #20015 Schema merge not completed for embeddings
Category: bug
Previous design specified that pr_embeddings and pr_memory_events should be merged into a single 'mem_ai_events' table, 

### #20013 Incorrect table name reference
Category: bug
Table name mismatch: code references 'mng_ai_tags_relations' but should be 'mem_ai_tags_relations'. This naming inconsis

### #20011 Missing tagging relations table implementation
Category: bug
Developer reports that mng_ai_tags_relations table is not implemented. The tagging functionality appears incomplete as e

### #20012 Embedding table merge not completed
Category: bug
pr_embeddings and pr_memory_events were supposed to be merged into a single mem_ai_events table, but this refactoring ap

### #20010 Ambiguous embedding method behavior
Category: bug
Confusion about embedding and chunking methods - developer questions whether using 3 embedding methods creates 3 duplica

### #20008 Missing embeddings-to-tagging connection
Category: bug
Developer states 'I would embedding to be connected to the tagging' indicating embeddings and tagging metadata are not p

### #20009 Documentation accuracy issue
Category: bug
The aicli_memory.md documentation file does not accurately reflect actual system flows. Developer asks if it 'shows the 

### #20007 Data source confusion - JSONL vs database
Category: bug
Developer questions whether the system is loading history from pr_prompts table or from JSONL files, suggesting the appr

### #20005 Memory loading source unclear
Category: bug
Uncertainty about whether the system is loading history from 'pr_prompts' or from JSONL files. Developer questions if JS

### #20006 Potential duplicate tables in schema
Category: bug
Developer mentions concerns about duplicate tables in the database (pr_events and pr_interactions), questioning whether 

### #20000 Database table naming inconsistency
Category: bug
Table name 'pr_interation' (or 'pr_interaction') was not renamed to 'pr_prompts' in the database schema, causing mismatc

### #20001 Missing table rename for junction table
Category: bug
Associated junction table 'pr_interation_tags' was not renamed to 'pr_prompts_tags', creating inconsistency in the datab

### #20002 Unclear data loading source
Category: bug
System behavior unclear regarding whether it loads history from 'pr_prompts' table or from JSONL files, with developer n

### #20003 Documentation out of sync with implementation
Category: bug
File 'aicli_memory.md' does not reflect actual flows and recent changes made to the system, requiring complete rewrite a

### #20004 Ambiguous embedding and chunking behavior
Category: bug
Unclear whether embedding with 3 different methods creates 3 separate database rows per prompt, and whether this only oc

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

### mcp
Category: feature
mcp

### tagging
Category: feature
tagging

### embeddings
Category: feature
embeddings

### auth
Category: feature
auth

### billing
Category: feature
billing

### graph-workflow
Category: feature
graph-workflow

### shared-memory
Category: feature
shared-memory

## Recent Session (2026-04-07 01:13)

• Ran `/memory` command to synchronize and update all memory_item files across the workspace
• Generated updated system files in workspace/_system/ directory (MEMORY.md, CLAUDE.md, rules.md, context.md, copilot.md)
• Copied refreshed memory files to code root and configuration directories (.cursor/rules/, .github/)
• Memory system now has current contextual data for Claude, Cursor, and AI CLI integrations
