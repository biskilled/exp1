"""
core/project_docs.py

Manages PROJECT.md in the working folder — a living project knowledge document
that is injected into CLAUDE.md so both the native claude CLI and aicli
always have full project context in the system prompt.

Structure of PROJECT.md:
  # PROJECT
  ## Use Case          — what it does, who uses it
  ## Architecture      — stack, key decisions, folder structure
  ## Features          — [x] done  /  [ ] in progress
  ## TODO / Next Steps — ordered by priority
  ## Recent Changes    — auto-updated by /docs generate
  ## Open Questions    — unresolved design decisions

Usage in aicli:
  docs = ProjectDocs(Path.cwd(), openai_agent)
  docs.generate(memory_snippets)   # OpenAI writes/updates the doc
  docs.add_todo("add dark mode")   # quick append without regeneration
  docs.read()                      # returns current text

Usage outside aicli (native claude CLI):
  PROJECT.md gets injected into CLAUDE.md by initialize_project()
  so claude reads it automatically as part of the system prompt.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path


TEMPLATE = """\
# PROJECT

## Use Case
<!-- Describe what this project does, for whom, and why it exists. -->

## Architecture
<!-- Key technical decisions, stack overview, folder structure. -->

## Features
<!-- Mark done items with [x]. Use [ ] for in-progress or planned. -->
- [ ] (none added yet)

## TODO / Next Steps
<!-- Ordered by priority. Add quickly with: /docs todo <item> -->

## Recent Changes
<!-- Auto-updated when you run /docs generate -->

## Open Questions
<!-- Unresolved design decisions or outstanding dependencies. -->
"""

_OPENAI_SYSTEM = (
    "You are a technical documentation writer. "
    "Output clean, concise Markdown only — no preamble, no commentary outside the document."
)


class ProjectDocs:

    def __init__(self, working_path: Path, openai_agent):
        self.path = working_path / "PROJECT.md"
        self.openai = openai_agent

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def read(self) -> str:
        if not self.path.exists():
            return ""
        return self.path.read_text(encoding="utf-8")

    def exists(self) -> bool:
        return self.path.exists() and bool(self.path.read_text().strip())

    # ------------------------------------------------------------------
    # Generate / update via OpenAI
    # ------------------------------------------------------------------

    def generate(self, memory_snippets: list[str] | None = None) -> str:
        """
        Use OpenAI to regenerate PROJECT.md from all available signals:
          - existing doc (preserved as base)
          - git log (last 40 commits)
          - recent memory snippets
        Writes the result to PROJECT.md and returns the new text.
        """
        existing = self.read() or TEMPLATE
        git_log = self._git_log()
        memory_block = "\n\n".join((memory_snippets or [])[:10]) or "(none)"

        user_prompt = f"""\
Update the PROJECT.md document below using the new context provided.

RULES:
- Preserve ALL checked checkboxes [x] — never uncheck a completed item.
- Preserve the user's own text in "Use Case", "Architecture", "Open Questions".
- Replace "Recent Changes" with a short, factual summary from the git log.
- Add newly detected TODO items to "TODO / Next Steps" — do not remove existing ones.
- Mark features as [x] done if the git log clearly shows they were completed.
- Do not invent anything not evidenced by the git log or memory snippets.
- Output the full updated document only. No text before or after it.

--- EXISTING PROJECT.md ---
{existing}

--- GIT LOG (last 40 commits) ---
{git_log}

--- RECENT CONTEXT (AI session memory) ---
{memory_block}

--- TODAY'S DATE ---
{datetime.now(timezone.utc).strftime('%Y-%m-%d')}
"""

        result = self.openai.send(_OPENAI_SYSTEM, user_prompt)
        result = result.strip()
        self.path.write_text(result + "\n", encoding="utf-8")
        return result

    # ------------------------------------------------------------------
    # Quick mutations (no OpenAI call)
    # ------------------------------------------------------------------

    def add_todo(self, item: str) -> None:
        """Append a TODO line under the ## TODO section without regenerating."""
        text = self.read() or TEMPLATE
        todo_line = f"- [ ] {item.strip()}"
        lines = text.splitlines()

        # Find ## TODO section and insert right after any existing items
        insert_at = None
        in_section = False
        for i, line in enumerate(lines):
            if line.startswith("## TODO"):
                in_section = True
                insert_at = i + 1
                continue
            if in_section and line.startswith("## "):
                # Reached the next section — insert before it
                break
            if in_section and line.strip():
                insert_at = i + 1  # keep moving insert point to end of section content

        if insert_at is not None:
            lines.insert(insert_at, todo_line)
        else:
            lines += ["", "## TODO / Next Steps", todo_line]

        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def mark_done(self, fragment: str) -> bool:
        """
        Mark the first TODO item whose text contains `fragment` as done.
        Returns True if an item was found and updated.
        """
        text = self.read()
        if not text:
            return False

        lines = text.splitlines()
        fragment_lower = fragment.lower()
        changed = False

        for i, line in enumerate(lines):
            if line.strip().startswith("- [ ]") and fragment_lower in line.lower():
                lines[i] = line.replace("- [ ]", "- [x]", 1)
                changed = True
                break

        if changed:
            self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        return changed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _git_log(self, n: int = 40) -> str:
        result = subprocess.run(
            ["git", "log", f"--max-count={n}",
             "--pretty=format:%h  %ad  %s", "--date=short"],
            capture_output=True, text=True,
        )
        return result.stdout.strip() or "(no git history)"
