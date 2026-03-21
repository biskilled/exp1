"""
gitops/git.py — Code-change extraction and git commit helpers.

Extracted from graph_runner so both the workflow engine and the work-item
pipeline can share these utilities without circular imports.

Public API:
    parse_code_changes(output) -> list[tuple[str, str]]
    apply_code_and_commit(code_dir, changes, node_name, run_id) -> str
    get_project_code_dir(project) -> str
"""
from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)

_EXTENSIONS = (
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".rs",
    ".rb", ".md", ".yaml", ".yml", ".json", ".toml", ".sh",
    ".css", ".html", ".sql", ".txt", ".env", ".cfg", ".ini",
)


def parse_code_changes(output: str) -> list[tuple[str, str]]:
    """Extract (file_path, content) pairs from LLM output.

    Recognized patterns:
      ### File: path/to/file.ext
      ```lang
      content
      ```
    Also handles:
      ## path/to/file.ext
      ```lang
      content
      ```
    """
    changes: list[tuple[str, str]] = []
    pattern = r"(?:###?\s+(?:File:\s*)?|##\s+)([^\n`]+?)\s*\n```(?:\w+)?\n(.*?)```"
    for m in re.finditer(pattern, output, re.DOTALL):
        path = m.group(1).strip().rstrip(":")
        content = m.group(2)
        if any(path.lower().endswith(ext) for ext in _EXTENSIONS) or "/" in path:
            if len(path) <= 200 and "\n" not in path:
                changes.append((path, content))
    return changes


def apply_code_and_commit(
    code_dir: str,
    changes: list[tuple[str, str]],
    node_name: str,
    run_id: str,
) -> str:
    """Write file changes to code_dir and run git add/commit/push.

    Returns the short commit hash on success, '' if nothing to commit,
    or an 'error: ...' string on failure.
    """
    base = Path(code_dir).resolve()

    wrote = 0
    for rel_path, content in changes:
        dest = (base / rel_path.lstrip("/")).resolve()
        if not str(dest).startswith(str(base)):
            log.warning(f"auto_commit: skipping traversal path {rel_path!r}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        log.info(f"auto_commit: wrote {rel_path}")
        wrote += 1

    if not wrote:
        log.info("auto_commit: no files written — skipping commit")
        return ""

    try:
        subprocess.run(["git", "add", "."], cwd=code_dir, check=True, capture_output=True)
        msg = f"auto: {node_name} [{run_id[:8]}]"
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=code_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        hash_r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=code_dir,
            capture_output=True,
            text=True,
        )
        commit_hash = hash_r.stdout.strip()
        subprocess.Popen(
            ["git", "push"],
            cwd=code_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info(f"auto_commit: committed {commit_hash} for node '{node_name}'")
        return commit_hash
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or b"").decode() if isinstance(e.stderr, bytes) else str(e.stderr or "")
        if "nothing to commit" in stderr or "nothing added" in stderr:
            return ""
        log.warning(f"auto_commit git error: {stderr[:200]}")
        return f"error: {stderr[:100]}"


def get_project_code_dir(project: str) -> str:
    """Return the code directory for a project.

    Reads project.yaml → code_dir; falls back to settings.code_dir.
    """
    from core.config import settings
    try:
        import yaml
        proj_yaml = Path(settings.workspace_dir) / project / "project.yaml"
        if proj_yaml.exists():
            cfg = yaml.safe_load(proj_yaml.read_text()) or {}
            if cfg.get("code_dir"):
                return str(cfg["code_dir"])
    except Exception:
        pass
    return settings.code_dir
