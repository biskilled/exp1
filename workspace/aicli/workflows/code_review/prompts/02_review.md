# Deep Code Review

Using the checklist above as a guide, perform a thorough code review.

Focus on:
- Bugs and logic errors
- Security vulnerabilities (injection, path traversal, secret exposure)
- Performance issues
- Missing type hints or incorrect types
- Unnecessary complexity

Output ONLY valid JSON:

```json
{
  "score": 7,
  "approved": false,
  "issues": ["description of each issue with file:line reference if possible"],
  "summary": "Overall assessment in 2-3 sentences."
}
```

Score 1-10. Approved if score >= 8.
