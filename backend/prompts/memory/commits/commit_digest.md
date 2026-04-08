Given a git commit message and context, produce a concise digest.
Return JSON only: {"summary": "1-2 sentence digest of what changed and why", "action_items": "", "importance": 5}
importance scale (0-10): 1-2=trivial/chore, 3-4=minor fix, 5-6=feature work, 7-8=significant change, 9-10=critical/architectural
No preamble, no markdown fences.
