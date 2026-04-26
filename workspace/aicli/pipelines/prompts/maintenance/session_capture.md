# Session Capture Prompt

Use this prompt at the **end of every development session** to record what was done.

---

You are maintaining the development history log for the **aicli** project.

## Task

Review the current session and write a structured log entry to append to `workspace/aicli/history/session_log.jsonl`.

### Steps

1. Summarise what was worked on in this session (2–5 bullet points, concrete and specific).
2. List every file that was created or modified (path + one-line description of the change).
3. Note any decisions made (architecture, design choices, things deferred).
4. Note any problems encountered and how they were resolved.
5. List any open items that need follow-up next session.

### Output Format

Write a single JSON object (one line) with this schema:
```json
{
  "ts": "2026-02-25T18:00:00",
  "session_summary": "Brief one-sentence description of session focus",
  "changes": [
    { "file": "path/to/file.py", "description": "what changed and why" }
  ],
  "decisions": [
    "Decision text"
  ],
  "problems_solved": [
    "Problem description → how it was resolved"
  ],
  "open_items": [
    "Follow-up task description"
  ]
}
```

### Context to inject

Before running this prompt, inject the following into context:
- `inject_files: [PROJECT.md]`
- Recent git log: `git log --oneline -10`
- Any files modified today: `git diff --name-only HEAD~1`

### Append to log

After generating the JSON entry, append it to:
```
workspace/aicli/history/session_log.jsonl
```
