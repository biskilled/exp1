Given N sequential prompt/response pairs, extract a digest capturing what was decided, built, or discovered.
Return JSON only: {"summary": "1-2 sentence digest", "action_items": "- bullet list of open action items, or empty string", "importance": 5}
importance scale (0-10): 1-2=trivial/chore, 3-4=debug/minor, 5-6=feature implementation, 7-8=architectural decision, 9-10=critical system design
No preamble, no markdown fences.
