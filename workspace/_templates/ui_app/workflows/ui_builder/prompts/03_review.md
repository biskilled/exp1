# UI Code Review

Review the UI implementation. Check:
- Accessibility (ARIA, keyboard navigation, focus management)
- Responsive design
- Event handler correctness (no memory leaks)
- Error/loading/empty state handling
- XSS safety (no innerHTML with user data)
- Performance (no unnecessary re-renders)

Output JSON: {"score": 1-10, "approved": bool, "issues": [...], "summary": "..."}
