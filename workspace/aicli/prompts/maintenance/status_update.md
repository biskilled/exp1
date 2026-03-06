# Project Status Update Prompt

Use this prompt to **update PROJECT.md** after a session of significant changes.
Run it via `/workflow update_docs` or manually with `/compare prompts/maintenance/status_update.md`.

---

You are a senior Python architect maintaining the **aicli** project documentation.

## Task

Update `workspace/aicli/PROJECT.md` to accurately reflect the current state of the project.

### What to update

1. **Features section**
   - Move any newly implemented items from `[ ]` to `[x]`
   - Add new items that were built but not yet listed
   - Remove items that are no longer relevant

2. **Architecture section**
   - Update module tables if new files were added
   - Update directory trees if structure changed
   - Fix any paths that are now stale

3. **Recent Changes table**
   - Add a row for today's date with a concise description of what changed
   - Keep the most recent 20 rows; trim older ones to "see git log"

4. **TODO / Next Steps**
   - Strike through (or remove) completed items
   - Add newly discovered items at the end
   - Reorder by priority if needed

5. **Open Questions**
   - Resolve any questions that have been answered
   - Add new questions that emerged

### Rules

- Be **factual** — only write what actually exists in the codebase
- Do **not** add features that are planned but not implemented
- Keep descriptions concise — one line per item
- Preserve the existing Markdown structure and heading levels

### Context to inject

```yaml
inject_files:
  - PROJECT.md
  - workspace/aicli/history/session_log.jsonl
```

Also read any files mentioned in the session log's `changes` list.

### Output

Return the complete updated `PROJECT.md` content. Do not truncate — return the full file.
Then write it to `workspace/aicli/PROJECT.md`.
