# FastAPI Code Review

Review the implementation for a FastAPI backend. Check:
- Correct HTTP status codes
- Pydantic v2 model usage
- Async/await correctness
- Missing error handling (404, 422, 500)
- SQL injection / security issues
- Test coverage

Output JSON only: {"score": 1-10, "approved": bool, "issues": [...], "summary": "..."}
