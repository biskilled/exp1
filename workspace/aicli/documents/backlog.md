# Backlog

> Review each use case group. Approve `[+]` items, reject `[-]`.
> Run `POST /memory/{project}/work-items/sync` to merge approved items into use cases.

 [ ] (auto) — discovery
<!-- G_SLUG: discovery -->
<!-- G_TYPE: existing -->
Total: 7 prompts
User tags:
AI existing:
AI new:

  PROMPTS P100472 [ ] [feature] [in-progress] [3] — Clean lifecycle tagging, implement AI suggestion counters, add ai_suggested tag

  PROMPTS P100431 [ ] [bug] [in-progress] [3] — Fix nested tag support and align pipeline with workflow infrastructure

  PROMPTS P100433 [ ] [bug] [in-progress] [3] — Fix inconsistent nested work display and clarify lifecycle project purpose

  PROMPTS P100473 [ ] [bug] [in-progress] [2] — Debug drag-and-drop and counter update functionality

  PROMPTS P100475 [ ] [bug] [in-progress] [2] — Remove lifecycle tags from bug/feature/task items as irrelevant

  PROMPTS P100423 [ ] [task] [in-progress] [2] — Document default pipeline configuration and restore parent-child work item linking

  PROMPTS P100474 [ ] [task] [in-progress] [1] — Evaluate lifecycle tag relevance and remove if unnecessary
---

26/03/17-20:36 [ ] (claude) — database-schema-refactor
<!-- G_SLUG: database-schema-refactor -->
<!-- G_TYPE: existing -->
Total: 39 prompts
User tags:
AI existing:
AI new:

  PROMPTS P100452 [ ] [feature] [completed] [4] — Auto-generate memory files from project facts and work items
    Requirements: R; e; g; e; n
    Deliveries: C; o; m; m; i

  PROMPTS P100478 [ ] [feature] [in-progress] [2] — Implement tagging mechanism for MRR with user-editable tags
    Requirements: A; d; d;  ; t
    Deliveries: D; e; s; i; g

  PROMPTS P100496 [ ] [feature] [in-progress] [2] — Create mng_projects table and refactor project_id references
    Requirements: C; r; e; a; t
    Deliveries: D; e; s; i; g

  PROMPTS P100449 [ ] [bug] [completed] [5] — Fix table name from mng_ai_tags_relations to mem_ai_tags_relations
    Requirements: R; e; n; a; m
    Deliveries: C; o; m; m; i

  PROMPTS P100480 [ ] [bug] [completed] [4] — Fix undefined column errors in route_entities and route_work_items
    Requirements: F; i; x;  ; p
    Deliveries: C; o; m; m; i

  PROMPTS P100481 [ ] [bug] [completed] [4] — Fix undefined column error in route_work_items for work_item_id
    Requirements: F; i; x;  ; p
    Deliveries: C; o; m; m; i

  PROMPTS P100501 [ ] [bug] [completed] [4] — Fix UPSERT conflict error in route_history line 470
    Requirements: F; i; x;  ; c
    Deliveries: C; o; m; m; i

  PROMPTS P100502 [ ] [bug] [completed] [4] — Fix duplicate constrained values error in commit sync
    Requirements: F; i; x;  ; O
    Deliveries: C; o; m; m; i

  PROMPTS P100434 [ ] [task] [in-progress] [2] — Remove unused tables and rename with mng_/cl_ prefixes
    Requirements: R; e; m; o; v
    Deliveries: I; d; e; n; t

  PROMPTS P100435 [ ] [task] [completed] [4] — Verify and apply database changes for table cleanup
    Requirements: C; o; n; f; i
    Deliveries: D; r; o; p; p

  PROMPTS P100447 [ ] [task] [completed] [4] — Merge pr_embeddings and pr_memory_events into mem_ai_events
    Requirements: M; e; r; g; e
    Deliveries: C; r; e; a; t

  PROMPTS P100453 [ ] [task] [completed] [3] — Document updated memory structure and tagging layers
    Requirements: U; p; d; a; t
    Deliveries: C; o; m; m; i

  PROMPTS P100454 [ ] [task] [completed] [4] — Merge pr_session_summeries into mem_ai_events with event_type
    Requirements: M; e; r; g; e
    Deliveries: C; o; m; m; i

  PROMPTS P100455 [ ] [task] [completed] [4] — Add llm_source and audit unused columns in mem_ai_events
    Requirements: A; d; d;  ; l
    Deliveries: C; o; m; m; i

  PROMPTS P100456 [ ] [task] [completed] [4] — Apply DDL changes and update database schema
    Requirements: E; x; e; c; u
    Deliveries: C; o; m; m; i

  PROMPTS P100457 [ ] [task] [completed] [4] — Refactor mem_ai_events tagging and remove unused columns
    Requirements: M; o; v; e;  
    Deliveries: C; o; m; m; i

  PROMPTS P100458 [ ] [task] [completed] [4] — Refactor mem_mrr_* tables to remove unused columns
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P100460 [ ] [task] [completed] [4] — Refactor mem_ai_* tables to remove duplicate columns
    Requirements: A; p; p; l; y
    Deliveries: C; o; m; m; i

  PROMPTS P100462 [ ] [task] [completed] [4] — Remove old migrations and reduce database.py file size
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P100468 [ ] [task] [completed] [3] — Review and clean up old table references from Database class
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P100477 [ ] [task] [completed] [4] — Verify table structure updates were applied
    Requirements: C; o; n; f; i
    Deliveries: C; o; m; m; i

  PROMPTS P100484 [ ] [task] [completed] [3] — Audit mem_ai_events and align tagging with MRR tables
    Requirements: M; o; v; e;  
    Deliveries: C; o; m; m; i

  PROMPTS P100485 [ ] [task] [in-progress] [2] — Reorder mem_ai_events and embedding columns, clean database.py
    Requirements: M; o; v; e;  
    Deliveries: I; d; e; n; t

  PROMPTS P100486 [ ] [task] [completed] [4] — Verify llm_source and embedding column reordering
    Requirements: C; o; n; f; i
    Deliveries: C; o; m; m; i

  PROMPTS P100487 [ ] [task] [completed] [4] — Create new mem_ai_events table and migrate data from old table
    Requirements: R; e; n; a; m
    Deliveries: C; o; m; m; i

  PROMPTS P100488 [ ] [task] [completed] [3] — Audit columns: doc_type, language, file_path usage
    Requirements: D; o; c; u; m
    Deliveries: C; o; m; m; i

  PROMPTS P100489 [ ] [task] [in-progress] [2] — Merge language into tags and refactor file_change column
    Requirements: A; d; d;  ; l
    Deliveries: D; e; s; i; g

  PROMPTS P100490 [ ] [task] [completed] [3] — Evaluate chunk and chunk_type columns for work_item usage
    Requirements: D; e; t; e; r
    Deliveries: C; o; m; m; i

  PROMPTS P100491 [ ] [task] [completed] [4] — Clean up invalid events and verify llm_source population
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P100497 [ ] [task] [completed] [3] — Verify prompts after client_id fix
    Requirements: V; a; l; i; d
    Deliveries: C; o; m; m; i

  PROMPTS P100504 [ ] [task] [completed] [4] — Audit mem_ai_work_items columns and alignment
    Requirements: D; e; t; e; r
    Deliveries: C; o; m; m; i

  PROMPTS P100575 [ ] [task] [in-progress] [2] — Reorder mem_ai_events columns per user specification
    Requirements: M; o; v; e;  
    Deliveries: D; e; s; i; g

  PROMPTS P100576 [ ] [task] [completed] [4] — Execute table migration with correct column order and drop _old table
    Requirements: M; i; g; r; a
    Deliveries: C; o; m; m; i

  PROMPTS P100577 [ ] [task] [completed] [3] — Evaluate importance column in mem_ai_events vs mem_ai_work_items
    Requirements: D; e; t; e; r
    Deliveries: I; d; e; n; t

  PROMPTS P100578 [ ] [task] [completed] [5] — Drop importance column from mem_ai_events
    Requirements: D; r; o; p;  
    Deliveries: C; o; m; m; i

  PROMPTS P100579 [ ] [task] [completed] [4] — Clean up corrupt event tags and backfill with user tags only
    Requirements: R; e; m; o; v
    Deliveries: C; o; m; m; i

  PROMPTS P100580 [ ] [task] [completed] [5] — Drop old tags and reorder mem_mrr_prompts columns
    Requirements: D; r; o; p;  
    Deliveries: C; o; m; m; i

  PROMPTS P100590 [ ] [task] [completed] [5] — Refactor user_id from UUID string to integer with updated_at
    Requirements: C; h; a; n; g
    Deliveries: C; o; m; m; i

  PROMPTS P100591 [ ] [task] [completed] [5] — Reorder table columns to standard schema: id→client_id→project_id→user_id
    Requirements: R; e; o; r; d
    Deliveries: C; o; m; m; i
---

26/03/10-03:14 [ ] (claude) — memory-layer-implementation
<!-- G_SLUG: memory-layer-implementation -->
<!-- G_TYPE: existing -->
Total: 49 prompts
User tags:
AI existing:
AI new:

  PROMPTS P100386 [ ] [feature] [in-progress] [0] — Are you using the mcp server in order to reciave all project information ? Also,

  PROMPTS P100392 [ ] [feature] [in-progress] [0] — can you run /memory, to make sure all updated. also can you check that system is

  PROMPTS P100400 [ ] [feature] [in-progress] [0] — let me summerise not. first run /memroy to update all sumeeries, db tagging and

  PROMPTS P100403 [ ] [feature] [in-progress] [0] — When I run memory through the aiCli - I did see some usefull suggestion that app

  PROMPTS P100411 [ ] [feature] [in-progress] [0] — now that there is porper tagging - can you make sure all is linked, mapped prope

  PROMPTS P100412 [ ] [feature] [in-progress] [0] — is it align to the 5 steps memory? is there is any addiotnal requirement in orde

  PROMPTS P100413 [ ] [feature] [in-progress] [0] — Is there is any addiotnal improvement that I can implemet for having full memroy

  PROMPTS P100414 [ ] [feature] [in-progress] [0] — 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many pr

  PROMPTS P100419 [ ] [feature] [in-progress] [0] — Can you run the /memory and go over current architecure - how data is stored, ho

  PROMPTS P100432 [ ] [feature] [in-progress] [0] — I would like to go over on all the feutre and plan propery to Planer and Worklow

  PROMPTS P100436 [ ] [feature] [in-progress] [0] — looks better. why memory_items and project_facts are under systeme managament ta

  PROMPTS P100437 [ ] [feature] [in-progress] [0] — I do see the table mng_session_tags, I also see session_tags.json file at the pr

  PROMPTS P100438 [ ] [feature] [in-progress] [0] — clean that up . also I do remember there was graph support for memroy usage, but

  PROMPTS P100439 [ ] [feature] [in-progress] [0] — I would like to make sure the client table are also aligned - for example mng_se

  PROMPTS P100440 [ ] [feature] [in-progress] [0] — I would like to know what do you think about the architecure ? Assuming there mi

  PROMPTS P100441 [ ] [feature] [in-progress] [0] — That is correct. it is bed pattern to use clinet name. there is already mng_user

  PROMPTS P100446 [ ] [feature] [in-progress] [0] — Is it makes more sense, before I continue to the secopnd phase (refactor embeddi

  PROMPTS P100448 [ ] [feature] [in-progress] [0] — I am not sure all tagging functionality is implemented as I do not see the mng_a

  PROMPTS P100450 [ ] [feature] [in-progress] [0] — I would like to make sure relation is managed properly.  relation can be managed

  PROMPTS P100451 [ ] [feature] [in-progress] [0] — I would like to make sure that the final layer include Work Items, Feature Snaps

  PROMPTS P100452 [ ] [feature] [in-progress] [0] — This task is related to current memory update (layer 1)  Create all memory files

  PROMPTS P100453 [ ] [feature] [in-progress] [0] — perfect. I would like to have an updated aicli_memory with all updated memory st

  PROMPTS P100493 [ ] [feature] [in-progress] [0] — I would like to build the aicli_memory.md for scratch in order to get a final vi

  PROMPTS P100494 [ ] [feature] [in-progress] [0] — About orocess_item / messeges - trigger in /memroy (for all new items at the mom

  PROMPTS P100510 [ ] [feature] [in-progress] [0] — can you update all memory_items (maybe run /memory) to have an uodated data

  PROMPTS P100512 [ ] [feature] [in-progress] [0] — Can you use aiCli_memeory to describe the followng : how flow works from mirror.

  PROMPTS P100513 [ ] [feature] [in-progress] [0] — Can you use aiCli_memeory to describe the followng : how flow works from mirror.

  PROMPTS P100514 [ ] [feature] [in-progress] [0] — In addtion to your reccomendation, I would like to check the following -  mem_ai

  PROMPTS P100515 [ ] [feature] [in-progress] [0] — dont you have any moemry, did you see the previous file you din - aicli_memoy.md

  PROMPTS P100516 [ ] [feature] [in-progress] [0] — I still see the columns in commit table - diif_summery and diff_details . is it

  PROMPTS P100517 [ ] [feature] [in-progress] [0] — I would like to understand the commit table - do you have my previous comment? m

  PROMPTS P100518 [ ] [feature] [in-progress] [0] — Where simple extraction flow can be something like that:  pr_tags_map   WHERE re

  PROMPTS P100521 [ ] [feature] [in-progress] [0] — can you explain where are the  prompts that used for update new commit ?

  PROMPTS P100522 [ ] [feature] [in-progress] [0] — Can you explain how commit data statitics are connected to work_items ? Is there

  PROMPTS P100523 [ ] [feature] [in-progress] [0] — three is link from prompts to commits. each five prompts summeries to event, whi

  PROMPTS P100528 [ ] [feature] [in-progress] [0] — I would like to understand how work_item are populated. work_item suppose to be

  PROMPTS P100545 [ ] [feature] [in-progress] [0] — Where are all the rpompts for ai_tags and work_item are ?

  PROMPTS P100546 [ ] [feature] [in-progress] [0] — I do see same work item working on mention document summery and update ai memory

  PROMPTS P100547 [ ] [feature] [in-progress] [0] — Can you share the quesry you are suing the get all promotps, commit, event per w

  PROMPTS P100552 [ ] [feature] [in-progress] [0] — now I dont see the counter or the promts. also, I still see work item   that  ar

  PROMPTS P100553 [ ] [feature] [in-progress] [0] — I still dont understand how there are work_items without any linked prompts. can

  PROMPTS P100558 [ ] [feature] [in-progress] [0] — I am not sre what is start_id used for . Also code_summenry - what is it for ? t

  PROMPTS P100559 [ ] [feature] [in-progress] [0] — I still dont understand what is summery column used for . also tags - I do see t

  PROMPTS P100560 [ ] [feature] [in-progress] [0] — What is summery used for, I do see ai_desc, what is summery for ?

  PROMPTS P100561 [ ] [feature] [in-progress] [0] — I think summery suppose to be part of ai_desc as there are alreadt 3 column for

  PROMPTS P100565 [ ] [feature] [in-progress] [0] — I am planning to add a layer that will merge planner_tags with wor_item - this l

  PROMPTS P100569 [ ] [feature] [in-progress] [0] — Feature_snapshot  I would like to create the final stage - mem_ai_feature_snapsh

  PROMPTS P100570 [ ] [feature] [in-progress] [0] — Assuming all will work properly. having a way to store all project history using

  PROMPTS P100575 [ ] [feature] [in-progress] [0] — Events - I would like to make sure events are working properly in order to have
---

26/03/10-00:52 [ ] (claude) — performance-optimization
<!-- G_SLUG: performance-optimization -->
<!-- G_TYPE: existing -->
Total: 8 prompts
User tags:
AI existing:
AI new:

  PROMPTS P100377 [ ] [feature] [completed] [2] — Design nested tag hierarchy (3+ levels) and optimize SQL query loading
    Requirements: o; p; t; i; m
    Deliveries: D; e; s; i; g

  PROMPTS P100427 [ ] [bug] [in-progress] [2] — Investigate slow project summary and history loading; add progress indicators
    Requirements: i; d; e; n; t
    Deliveries: S; a; n; i; t

  PROMPTS P100551 [ ] [bug] [completed] [3] — Fix query performance regression; clarify DIGEST column vs event counter; resolve orphan work items
    Requirements: e; x; p; l; a
    Deliveries: r; o; u; t; e

  PROMPTS P100587 [ ] [bug] [completed] [4] — Fix prompt history loading to show all entries from database instead of stale session files
    Requirements: l; o; a; d;  
    Deliveries: r; o; u; t; e

  PROMPTS P100588 [ ] [bug] [completed] [4] — Fix stale session ID persisting on load; clean legacy context files
    Requirements: s; t; o; p;  
    Deliveries: c; h; a; t; .

  PROMPTS P100589 [ ] [bug] [completed] [4] — Eliminate 15-second delay before loading correct current session on startup
    Requirements: l; o; a; d;  
    Deliveries: c; h; a; t; .

  PROMPTS P100376 [ ] [performance-optimization] [completed] [4] — Implement tag caching to reduce database calls on project access
    Requirements: a; v; o; i; d
    Deliveries: c; h; a; t; .

  PROMPTS P100550 [ ] [performance-optimization] [completed] [4] — Add composite indexes for planner tabs/work items; enforce top-level query documentation
    Requirements: o; p; t; i; m
    Deliveries: d; b; _; m; i
---

26/04/01-01:17 [ ] (claude_cli) — work-items-management
<!-- G_SLUG: work-items-management -->
<!-- G_TYPE: existing -->
Total: 31 prompts
User tags:
AI existing:
AI new:

  PROMPTS P100464 [ ] [feature] [completed] [4] — Add embeddings to project_facts and work_items memory layers
    Requirements: A; d; d;  ; e
    Deliveries: U; p; d; a; t

  PROMPTS P100476 [ ] [feature] [completed] [4] — Reorganize bug/AI tags structure and add main category section
    Requirements: M; o; v; e;  
    Deliveries: A; d; d; e; d

  PROMPTS P100499 [ ] [feature] [in-progress] [2] — Show full prompts and LLM responses in history with copy functionality
    Requirements: D; i; s; p; l
    Deliveries: U; p; d; a; t

  PROMPTS P100506 [ ] [feature] [completed] [4] — Add drag-drop work_items between tags and resize bottom panel
    Requirements: E; n; a; b; l
    Deliveries: U; p; d; a; t

  PROMPTS P100509 [ ] [feature] [completed] [4] — Add work_item move-back and merge-into-workitem functionality
    Requirements: M; o; v; e;  
    Deliveries: C; l; e; a; r

  PROMPTS P100529 [ ] [feature] [completed] [4] — Add work_item row columns for name, prompts, commits, date with sorting
    Requirements: A; d; d;  ; c
    Deliveries: U; p; d; a; t

  PROMPTS P100531 [ ] [feature] [completed] [4] — Add work_items columns to lower screen Planner tab
    Requirements: D; i; s; p; l
    Deliveries: U; p; d; a; t

  PROMPTS P100534 [ ] [feature] [in-progress] [2] — Implement work_item delete handler function
    Requirements: D; e; f; i; n
    Deliveries: V; e; r; i; f

  PROMPTS P100535 [ ] [feature] [completed] [4] — Add sticky header and AI tag suggestions to work_items
    Requirements: M; a; k; e;  
    Deliveries: U; p; d; a; t

  PROMPTS P100536 [ ] [feature] [completed] [4] — Display AI tag suggestions on each work_item row
    Requirements: S; h; o; w;  
    Deliveries: U; p; d; a; t

  PROMPTS P100538 [ ] [feature] [completed] [4] — Format AI tag suggestions as category:name (e.g., bug:auth)
    Requirements: S; h; o; w;  
    Deliveries: U; p; d; a; t

  PROMPTS P100542 [ ] [feature] [completed] [5] — Improve AI tag suggestion hierarchy and fallback logic
    Requirements: S; u; g; g; e
    Deliveries: U; p; d; a; t

  PROMPTS P100500 [ ] [bug] [completed] [4] — Fix history to display both prompts and LLM responses
    Requirements: R; e; s; t; o
    Deliveries: V; e; r; i; f

  PROMPTS P100507 [ ] [bug] [in-progress] [3] — Fix drag-drop hover highlighting and linked display issues
    Requirements: F; i; x;  ; o

  PROMPTS P100508 [ ] [bug] [completed] [4] — Fix work_item display after drag-drop to tag
    Requirements: W; o; r; k; _
    Deliveries: F; i; x; e; d

  PROMPTS P100524 [ ] [bug] [completed] [4] — Fix missing ai_tags column in work_items query
    Requirements: A; d; d;  ; m
    Deliveries: C; r; e; a; t

  PROMPTS P100526 [ ] [bug] [completed] [4] — Fix tag properties panel not displaying on tag click
    Requirements: S; h; o; w;  
    Deliveries: F; i; x; e; d

  PROMPTS P100530 [ ] [bug] [completed] [3] — Fix UI changes not visible after code update
    Requirements: E; n; s; u; r
    Deliveries: I; n; s; t; r

  PROMPTS P100537 [ ] [bug] [completed] [4] — Fix work_item click drawer and improve UI spacing/font size
    Requirements: F; i; x;  ; w
    Deliveries: A; d; d; e; d

  PROMPTS P100539 [ ] [bug] [completed] [4] — Fix missing tags display and use full row width for description
    Requirements: R; e; s; t; o
    Deliveries: U; p; d; a; t

  PROMPTS P100540 [ ] [bug] [completed] [4] — Fix last column visibility and add tag type labels
    Requirements: R; e; s; t; o
    Deliveries: U; p; d; a; t

  PROMPTS P100544 [ ] [bug] [completed] [5] — Fix AI tag suggestions showing empty and add refresh button
    Requirements: S; h; o; w;  
    Deliveries: F; i; x; e; d

  PROMPTS P100552 [ ] [bug] [completed] [4] — Fix work_item counter and commit counts display
    Requirements: S; h; o; w;  
    Deliveries: F; i; x; e; d

  PROMPTS P100557 [ ] [bug] [completed] [4] — Fix work_items disappearing when adding AI tags
    Requirements: W; o; r; k; _
    Deliveries: F; i; x; e; d

  PROMPTS P100504 [ ] [task] [completed] [4] — Audit work_items table columns and define usage purpose
    Requirements: C; l; a; r; i
    Deliveries: C; o; m; p; l

  PROMPTS P100527 [ ] [task] [completed] [2] — Assess cost of populating mem_mrr_commits_code per commit
    Requirements: E; v; a; l; u
    Deliveries: C; o; s; t;  

  PROMPTS P100532 [ ] [task] [completed] [4] — Improve work_items table header clarity and column spacing
    Requirements: W; i; d; e; n
    Deliveries: U; p; d; a; t

  PROMPTS P100533 [ ] [task] [completed] [4] — Format date to yy/mm/dd-hh:mm and filter non-work_item tags
    Requirements: C; h; a; n; g
    Deliveries: U; p; d; a; t

  PROMPTS P100541 [ ] [task] [completed] [4] — Add left padding, fix date format, and implement AI tag suggestions
    Requirements: A; d; d;  ; l
    Deliveries: F; i; x; e; d

  PROMPTS P100543 [ ] [task] [completed] [4] — Investigate why work_item #20006 appears as last updated
    Requirements: E; x; p; l; a
    Deliveries: I; d; e; n; t

  PROMPTS P100545 [ ] [task] [completed] [2] — Document AI tag suggestion and work_item prompt locations
    Requirements: L; o; c; a; t
    Deliveries: D; o; c; u; m
---

26/03/09-04:08 [ ] (claude) — ui-bugs-and-fixes
<!-- G_SLUG: ui-bugs-and-fixes -->
<!-- G_TYPE: existing -->
Total: 97 prompts
User tags:
AI existing:
AI new:

  PROMPTS P100374 [ ] [bug] [in-progress] [0] — I think there is an issue with ui as it is not loading properly (and I do see er

  PROMPTS P100375 [ ] [bug] [in-progress] [0] — I am shutting down elecrotn and run fresh - but cannot see anythin. also when wh

  PROMPTS P100378 [ ] [bug] [in-progress] [0] — yes. just to clarify when I add login - it will be first level only ?

  PROMPTS P100379 [ ] [bug] [in-progress] [0] — yes

  PROMPTS P100381 [ ] [bug] [in-progress] [0] — why there is sometime problem to restart the app (I do see that beckend is exite

  PROMPTS P100382 [ ] [bug] [in-progress] [0] — I do see the save button - and when I save I do see the tag, when I am checking

  PROMPTS P100383 [ ] [bug] [in-progress] [0] — Where do I click accept , is it in the Chat at the top ? I dont see that

  PROMPTS P100404 [ ] [bug] [in-progress] [0] — There is still UI issue with updateting/ showing the correct phase per session.

  PROMPTS P100405 [ ] [bug] [in-progress] [0] — The error still exists - When I change the phase (on chats) - I am not able to s

  PROMPTS P100406 [ ] [bug] [in-progress] [0] — Issue is not fixed - In Chat - I cannot change/update phase. also most chat sess

  PROMPTS P100407 [ ] [bug] [in-progress] [0] — Lets try to fix the first bug in the Chat session as it is not fixed. when I upl

  PROMPTS P100408 [ ] [bug] [in-progress] [0] — I still do not see that fixed. the session that mandtory fields are not updates

  PROMPTS P100409 [ ] [bug] [in-progress] [0] — That looks better. the problem now is that on any change of the phase the sessio

  PROMPTS P100444 [ ] [bug] [in-progress] [0] — Looks beter. there are some minor issue - in project page, I do see in Recent ai

  PROMPTS P100471 [ ] [bug] [in-progress] [0] — I do see some errors in the ui - column "event_type" does not exist - line 228 i

  PROMPTS P100479 [ ] [bug] [in-progress] [0] — When I am adding tags I do see in the UI error [object object] - not the real st

  PROMPTS P100499 [ ] [bug] [in-progress] [0] — Now I started to see prompts, but I do see in history just small text instead of

  PROMPTS P100500 [ ] [bug] [in-progress] [0] — Histroy used to show promp and llm response . I currently see only prompt

  PROMPTS P100530 [ ] [bug] [in-progress] [0] — I do not see any change at the ui.

  PROMPTS P100537 [ ] [bug] [in-progress] [0] — Work_item not loading the details when I click on work item. also in the ui - I

  PROMPTS P100539 [ ] [bug] [in-progress] [0] — I dont see any tags at the rows now (not ai and not users). also I do that desc

  PROMPTS P100540 [ ] [bug] [in-progress] [0] — I cannot see the last column now. all I see is the first column name (commits..

  PROMPTS P100554 [ ] [bug] [in-progress] [0] — In the ui - when I accept AI tag - configrm should be remove (only delete suppos

  PROMPTS P100573 [ ] [bug] [in-progress] [0] — It looks like the ui not working properly. In planner I do see any bug/ category

  PROMPTS P100574 [ ] [bug] [in-progress] [0] — Seems that electron is loadinng emtpty

  PROMPTS P100581 [ ] [bug] [in-progress] [0] — I still dont see the changes in the ui. also do not see the latest prompts I am

  PROMPTS P100582 [ ] [bug] [in-progress] [0] — I startrd to see the latest prompts which is good. I do not see on each promot t

  PROMPTS P100583 [ ] [bug] [in-progress] [0] — I still do not see the change in the chat tab. I do see the 5 last digit in the

  PROMPTS P100585 [ ] [bug] [in-progress] [0] — I understand the issue. you have worked on Tab prompts in history and I am reffe

  PROMPTS P100586 [ ] [bug] [in-progress] [0] — lloks better . the session_id on the right panel is shown not on the top. (can y

  PROMPTS P100371 [ ] [bug] [in-progress] [0] — Assuming I will improve the project management page, workflow processes. can you

  PROMPTS P100372 [ ] [bug] [in-progress] [0] — The last prompts was asking for a new feature (clinet install/ support multiple

  PROMPTS P100384 [ ] [bug] [in-progress] [0] — can you run /memory, and make the UI more clear. add your sujjestion in a clear

  PROMPTS P100385 [ ] [bug] [in-progress] [0] — can you run /memory and run some tests? I do not see any sujjestion on all the e

  PROMPTS P100387 [ ] [bug] [in-progress] [0] — hellow, how are you ?

  PROMPTS P100388 [ ] [bug] [in-progress] [0] — I understand the issue. I am using your claude cli and hooks to store propts and

  PROMPTS P100389 [ ] [bug] [in-progress] [0] — I am siting with my freid and try to explain him wha is this system is about ? c

  PROMPTS P100390 [ ] [bug] [in-progress] [0] — I do have some concern how commit/hash are linked to prompts/llm answers. also a

  PROMPTS P100391 [ ] [bug] [in-progress] [0] — I do see the option to add tag in history - can you make sure all tags are loade

  PROMPTS P100393 [ ] [bug] [in-progress] [0] — I do see that there is a link between commit and session ID. is it possible to h

  PROMPTS P100394 [ ] [bug] [in-progress] [0] — I do see session_tags.json - is it used ? Also - history.jsonl start to be very

  PROMPTS P100395 [ ] [bug] [in-progress] [0] — Something wit hooks is not working now, as I do not see any new prompts / llm re

  PROMPTS P100396 [ ] [bug] [in-progress] [0] — Pagination - I do see now in the chat only 24 prompts (there are much more) can

  PROMPTS P100397 [ ] [bug] [in-progress] [0] — Taggin - there is a wau to add tags in History, commit and chat - which is good.

  PROMPTS P100398 [ ] [bug] [in-progress] [0] — Let me summersie and make sure all work properly - tags (per session) - can be a

  PROMPTS P100399 [ ] [bug] [in-progress] [0] — Currently the commit tags in Chat are all on a session phase. I would like to li

  PROMPTS P100401 [ ] [bug] [in-progress] [0] — I would like to set that up , and also add that to new prokect as autoamted set

  PROMPTS P100402 [ ] [bug] [in-progress] [0] — The last commit was b255366 which suppose to be linked to the last prompt. it di

  PROMPTS P100410 [ ] [bug] [in-progress] [0] — It looks good and working as expected. the issue now is how it is linked to Hist

  PROMPTS P100415 [ ] [bug] [in-progress] [0] — I would like to optimise the code : check each file, make sure code is in used a

  PROMPTS P100416 [ ] [bug] [in-progress] [0] — I have started to look in some other solution like https://github.com/danshapiro

  PROMPTS P100417 [ ] [bug] [in-progress] [0] — After this refactor - can you check if tags are well used ? is memroy improved b

  PROMPTS P100418 [ ] [bug] [in-progress] [0] — Can you summersie all improvement - would that make the systme better perfromed

  PROMPTS P100420 [ ] [bug] [in-progress] [0] — Keys are stored at my .env file which you can load - for claude api the key is u

  PROMPTS P100421 [ ] [bug] [in-progress] [0] — are you using the mcp now?

  PROMPTS P100422 [ ] [bug] [in-progress] [0] — I would like to start working on the workflows - the goal is to be able to be si

  PROMPTS P100424 [ ] [bug] [in-progress] [0] — I do mention to sotre the prompts in database, would there be a way to change th

  PROMPTS P100425 [ ] [bug] [in-progress] [0] — yes

  PROMPTS P100426 [ ] [bug] [in-progress] [0] — can you use the mcp tool and explain what the prject is about ?

  PROMPTS P100428 [ ] [bug] [in-progress] [0] — In the project I used to see the aiCli project, and I do not see that now. also

  PROMPTS P100429 [ ] [bug] [in-progress] [0] — can you use the mcp tool and explain what the code is doing ?

  PROMPTS P100430 [ ] [bug] [in-progress] [0] — What is the claude agent sdk is uded for can it be used for my use cases for mut

  PROMPTS P100442 [ ] [bug] [in-progress] [0] — it looks like it is a bit broken, I have got an error - '_Database' object has n

  PROMPTS P100443 [ ] [bug] [in-progress] [0] — There are some error - on the first load, it lookls like Backend is failing (aft

  PROMPTS P100445 [ ] [bug] [in-progress] [0] — Few more strucure - users are also part of client (client can have mutiple users

  PROMPTS P100459 [ ] [bug] [in-progress] [0] — test prompt after migration

  PROMPTS P100461 [ ] [bug] [in-progress] [0] — test after mem_ai cleanup

  PROMPTS P100463 [ ] [bug] [in-progress] [0] — Implement 1 and 2. pipeline is trigerred from the planer tab. for example there

  PROMPTS P100465 [ ] [bug] [in-progress] [0] — Not sure if you remember the previous memory config. if you do (you can check ai

  PROMPTS P100466 [ ] [bug] [in-progress] [0] — yes . fix that all

  PROMPTS P100467 [ ] [bug] [in-progress] [0] — I would like to create a new feature - merge tags in the ui. in order to be able

  PROMPTS P100469 [ ] [bug] [in-progress] [0] — Under backend folder, I do see a workspace foldr. is it used ?

  PROMPTS P100470 [ ] [bug] [in-progress] [0] — plese delete that

  PROMPTS P100482 [ ] [bug] [in-progress] [0] — Looks like bug are fixed, and commit, prompts loading fast, but there is not con

  PROMPTS P100483 [ ] [bug] [in-progress] [0] — I have got an error on /history/commits/sync?project=aicli rest api in     execu

  PROMPTS P100492 [ ] [bug] [in-progress] [0] — Yes please. about Sho llm in the ui - make it visible tag

  PROMPTS P100495 [ ] [bug] [in-progress] [0] — test prompt after fix

  PROMPTS P100498 [ ] [bug] [in-progress] [0] — final verify prompt

  PROMPTS P100503 [ ] [bug] [in-progress] [0] — I am checking the aiCli_memory - and it is looks likje it is not updated at all.

  PROMPTS P100505 [ ] [bug] [in-progress] [0] — I do see an issue - Uncaught ReferenceError: _plannerSelectAiSubtype is not defi

  PROMPTS P100511 [ ] [bug] [in-progress] [0] — I do have some errors loading data - route_work_items line 249 - cur.execute(_SQ

  PROMPTS P100519 [ ] [bug] [in-progress] [0] — I do not see any update at the database

  PROMPTS P100520 [ ] [bug] [in-progress] [0] — yes please

  PROMPTS P100525 [ ] [bug] [in-progress] [0] — I would like to sapparte database.py in order to have methgods and tables schema

  PROMPTS P100548 [ ] [bug] [in-progress] [0] — before you desing. is it possible to add some mechanism to our converstion. for

  PROMPTS P100549 [ ] [bug] [in-progress] [0] — I have just tried that, got unknow skill /tag. do I have to open a new session ?

  PROMPTS P100555 [ ] [bug] [in-progress] [0] — can I add tags  here for my prompts using /tag or I need to use a new session ?

  PROMPTS P100556 [ ] [bug] [in-progress] [0] — I always get an error saying ynknow skill tag.

  PROMPTS P100562 [ ] [bug] [in-progress] [0] — I would like to woek on planner_tag. can you change the tag to feature:planner

  PROMPTS P100563 [ ] [bug] [in-progress] [0] — I am looking on planner_tag table. seq_num - never populated. is it needed? sour

  PROMPTS P100564 [ ] [bug] [in-progress] [0] — Yes. please about createor - it must be woth a value . if user create it will be

  PROMPTS P100566 [ ] [bug] [in-progress] [0] — yes

  PROMPTS P100567 [ ] [bug] [in-progress] [0] — This start to look good. I would like to add one more column - deliveries that w

  PROMPTS P100568 [ ] [bug] [in-progress] [0] — can you add tag feature:feature_snapshot

  PROMPTS P100571 [ ] [bug] [in-progress] [0] — How can I improve points 4 and 5 ? for point 4 - I did make prompts in sappasret

  PROMPTS P100572 [ ] [bug] [in-progress] [0] — ok. can you implement that. make sure dashboard is a new tab. pipeline will be a

  PROMPTS P100584 [ ] [bug] [in-progress] [0] — test: is hook-log working now after m050?

>>>>>>> REJECTED <<<<<<

PROMPTS P100380 [-] [feature] [completed] [4] — Improve action button visibility and add archive/restore functionality via menu
  <!-- Rejected: 2026-04-18 -->
