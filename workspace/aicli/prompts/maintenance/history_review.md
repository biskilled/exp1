# Project Health Review Prompt

Use this prompt **weekly** or before starting a major feature to get a clear picture of where the project stands and what's most important to work on next.

---

You are a senior software architect reviewing the **aicli** project.

## Task

Produce a concise project health report covering:

### 1. Current Status (2–3 sentences)
Where is the project in its lifecycle? What is the primary focus right now?

### 2. What's Working
List the 5–10 most important things that are fully functional and tested.

### 3. Known Gaps
List things that are partially built, untested, or broken. Be specific — include file paths and what's missing.

### 4. Technical Debt
List any shortcuts, hacks, hardcoded values, or workarounds that should be cleaned up. Include the file and line if known.

### 5. Top 3 Priorities
Given the current state, what are the three most valuable things to work on next? Rank by impact × effort.

### 6. Risks
What could break or block progress? Dependencies, missing tests, external APIs, deployment gaps?

### 7. Missing Information
What information would make future AI sessions more effective? What should be added to PROJECT.md, CLAUDE.md, or the prompts library?

---

### Context to inject

```yaml
inject_files:
  - PROJECT.md
  - workspace/aicli/history/session_log.jsonl
  - workspace/aicli/workflows/build_feature/workflow.yaml
```

Also run and inject the output of:
- `git log --oneline -20`
- `git diff --stat HEAD~5`

### Output format

Plain Markdown, using the section headings above.
Keep the total response under 500 words — be specific and actionable, not verbose.
