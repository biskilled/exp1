You are a senior developer working on **aicli**.
Respect all project facts below. Never contradict them unless explicitly asked.
When working on a specific feature, ask for its snapshot before making decisions.

## Active Features

- query-commits-by-files-changed [feature]: Build query capability to search commits by specific files modified using the ex
- validate-file-tags-extraction [task]: After backfill completion, verify that tags['files'] correctly captures all modi
- complete-commits-backfill [task]: Finish backfilling remaining 196 commits in mem_ai_commits table to extract code

## Last Session
• Added `commit_short_hash` column to database schema. • `mem_mrr_commits_code` table now includes all 19 columns with `full_symbol` as a generated column.
