"""
memory_code_parser.py — Tree-sitter AST parser for per-symbol commit code stats.

Parses a git commit diff using tree-sitter to produce one row per changed
symbol (class / method / function) per file.  Results are written into
mem_mrr_commits_code.  Called as a background task after each commit is stored.

Public API::

    count = await extract_commit_code(project, commit_hash)
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
from pathlib import Path
from typing import Optional

from core.config import settings
from core.database import db
from core.prompt_loader import prompts as _prompts

log = logging.getLogger(__name__)

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_GET_COMMIT_META = """
    SELECT tags, project_id FROM mem_mrr_commits
    WHERE commit_hash=%s AND project_id=%s
"""

_SQL_GET_CODE_DIR = """
    SELECT code_dir FROM mng_projects WHERE id=%s AND code_dir IS NOT NULL LIMIT 1
"""

_SQL_UPSERT_CODE_ROW = """
    INSERT INTO mem_mrr_commits_code
        (client_id, project_id, commit_hash, file_path, file_ext, file_language,
         file_change, symbol_type, class_name, method_name, symbol_change,
         rows_added, rows_removed, diff_snippet, llm_summary)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON CONFLICT (commit_hash, file_path, symbol_type,
                 COALESCE(class_name,''), COALESCE(method_name,'')) DO NOTHING
"""

# ── Language detection ─────────────────────────────────────────────────────────

_EXT_TO_LANG: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
}

_SUPPORTED_LANGS = {"python", "javascript", "typescript", "go", "rust", "java", "ruby"}


def _detect_language(file_ext: str) -> str:
    """Return language string from file extension, or '' if unsupported."""
    return _EXT_TO_LANG.get(file_ext.lower(), "")


def _get_tree_sitter_parser(language: str):
    """Return a tree-sitter Parser for the given language, or None if unavailable."""
    if language not in _SUPPORTED_LANGS:
        return None
    try:
        from tree_sitter_languages import get_parser
        return get_parser(language)
    except Exception as e:
        log.debug(f"_get_tree_sitter_parser({language}): {e}")
        return None


# ── Symbol extraction ──────────────────────────────────────────────────────────

def _extract_symbols_from_source(source: str, language: str) -> list[dict]:
    """Walk tree-sitter AST and return symbol defs with line ranges.

    Returns list of::
        {"symbol_type": "class"|"method"|"function",
         "name": str, "class_name": str|None,
         "start_line": int, "end_line": int}
    Line numbers are 0-based (matching tree-sitter convention).
    """
    parser = _get_tree_sitter_parser(language)
    if parser is None:
        return []
    try:
        tree = parser.parse(source.encode("utf-8", errors="replace"))
    except Exception as e:
        log.debug(f"_extract_symbols_from_source parse error: {e}")
        return []

    symbols: list[dict] = []
    root = tree.root_node

    def _walk(node, current_class: str | None = None) -> None:
        """Recursively walk AST nodes."""
        node_type = node.type

        if language == "python":
            if node_type == "class_definition":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                symbols.append({
                    "symbol_type": "class",
                    "name": name,
                    "class_name": None,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })
                for child in node.children:
                    _walk(child, current_class=name)
                return  # children already walked
            elif node_type == "function_definition":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                stype = "method" if current_class else "function"
                symbols.append({
                    "symbol_type": stype,
                    "name": name,
                    "class_name": current_class,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })

        elif language in ("javascript", "typescript"):
            if node_type in ("class_declaration", "class_expression"):
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                symbols.append({
                    "symbol_type": "class",
                    "name": name,
                    "class_name": None,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })
                for child in node.children:
                    _walk(child, current_class=name)
                return
            elif node_type in ("function_declaration", "function_expression",
                               "arrow_function", "method_definition"):
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                stype = "method" if current_class else "function"
                if name:
                    symbols.append({
                        "symbol_type": stype,
                        "name": name,
                        "class_name": current_class,
                        "start_line": node.start_point[0],
                        "end_line": node.end_point[0],
                    })

        elif language == "go":
            if node_type == "type_spec":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                symbols.append({
                    "symbol_type": "class",
                    "name": name,
                    "class_name": None,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })
            elif node_type in ("function_declaration", "method_declaration"):
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                recv_node = node.child_by_field_name("receiver")
                recv_type = ""
                if recv_node:
                    # Extract receiver type name
                    for c in recv_node.children:
                        if c.type == "parameter_declaration":
                            for cc in c.children:
                                if cc.type in ("type_identifier", "pointer_type"):
                                    recv_type = cc.text.decode().lstrip("*")
                                    break
                symbols.append({
                    "symbol_type": "method" if recv_type else "function",
                    "name": name,
                    "class_name": recv_type or None,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })

        elif language == "rust":
            if node_type == "impl_item":
                type_node = node.child_by_field_name("type")
                type_name = type_node.text.decode() if type_node else ""
                symbols.append({
                    "symbol_type": "class",
                    "name": type_name,
                    "class_name": None,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })
                for child in node.children:
                    _walk(child, current_class=type_name)
                return
            elif node_type == "function_item":
                name_node = node.child_by_field_name("name")
                name = name_node.text.decode() if name_node else ""
                stype = "method" if current_class else "function"
                symbols.append({
                    "symbol_type": stype,
                    "name": name,
                    "class_name": current_class,
                    "start_line": node.start_point[0],
                    "end_line": node.end_point[0],
                })

        for child in node.children:
            _walk(child, current_class=current_class)

    _walk(root)
    return symbols


# ── Diff parsing ───────────────────────────────────────────────────────────────

def _parse_diff_for_file(diff_section: str) -> dict:
    """Extract file info and changed line numbers from a single file's diff section.

    Returns::
        {"file_path": str, "file_change": str,
         "added_lines": set[int], "removed_lines": set[int]}
    Line numbers are 1-based (unified diff convention).
    """
    lines = diff_section.splitlines()

    # Determine change type
    file_change = "modified"
    for line in lines[:10]:
        if line.startswith("new file mode"):
            file_change = "added"
        elif line.startswith("deleted file mode"):
            file_change = "deleted"
        elif line.startswith("rename"):
            file_change = "renamed"

    # Extract file path (b-side)
    file_path = ""
    for line in lines:
        if line.startswith("+++ b/"):
            file_path = line[6:]
            break
        elif line.startswith("+++ /dev/null"):
            file_change = "deleted"

    if not file_path:
        for line in lines:
            if line.startswith("--- a/"):
                file_path = line[6:]
                break

    # Parse @@ hunks to find changed line numbers
    added_lines: set[int] = set()
    removed_lines: set[int] = set()
    new_lineno = 0
    old_lineno = 0

    hunk_re = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
    for line in lines:
        m = hunk_re.match(line)
        if m:
            old_lineno = int(m.group(1))
            new_lineno = int(m.group(2))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.add(new_lineno)
            new_lineno += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.add(old_lineno)
            old_lineno += 1
        else:
            new_lineno += 1
            old_lineno += 1

    return {
        "file_path": file_path,
        "file_change": file_change,
        "added_lines": added_lines,
        "removed_lines": removed_lines,
    }


def _extract_diff_snippet(diff_lines: list[str], symbol_start: int, symbol_end: int,
                          max_chars: int = 500) -> str:
    """Extract diff lines that fall within a symbol's line range, capped to max_chars."""
    # diff_lines contains the full hunk lines with +/-/space prefixes
    # We rebuild line numbers from @@ headers
    snippet_lines: list[str] = []
    new_lineno = 0
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

    for line in diff_lines:
        m = hunk_re.match(line)
        if m:
            new_lineno = int(m.group(1))
            continue
        if line.startswith("+") and not line.startswith("+++"):
            if symbol_start <= new_lineno <= symbol_end + 2:
                snippet_lines.append(line)
            new_lineno += 1
        elif line.startswith("-") and not line.startswith("---"):
            pass  # removed lines: no advance of new_lineno
        else:
            new_lineno += 1

    snippet = "\n".join(snippet_lines)
    return snippet[:max_chars]


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _claude_key() -> Optional[str]:
    try:
        from data.dl_api_keys import get_key
        return get_key("claude") or get_key("anthropic") or None
    except Exception:
        return None


async def _haiku(system: str, user: str, max_tokens: int = 120) -> str:
    key = _claude_key()
    if not key:
        return ""
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=key)
        resp = await client.messages.create(
            model=settings.haiku_model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return (resp.content[0].text if resp.content else "").strip()
    except Exception as e:
        log.debug(f"_haiku error: {e}")
        return ""


# ── YAML guards ────────────────────────────────────────────────────────────────

def _read_yaml_guards(project: str) -> dict:
    """Read commit_code_extraction config from workspace/{project}/project.yaml."""
    defaults = {"min_lines": 5, "only_on_commits_with_tags": False}
    try:
        import yaml
        proj_yaml = Path(settings.workspace_dir) / project / "project.yaml"
        if proj_yaml.exists():
            cfg = yaml.safe_load(proj_yaml.read_text()) or {}
            ext = cfg.get("commit_code_extraction", {}) or {}
            defaults["min_lines"] = int(ext.get("min_lines", 5))
            defaults["only_on_commits_with_tags"] = bool(ext.get("only_on_commits_with_tags", False))
    except Exception as e:
        log.debug(f"_read_yaml_guards error: {e}")
    return defaults


# ── Main entry point ───────────────────────────────────────────────────────────

async def extract_commit_code(project: str, commit_hash: str) -> int:
    """Parse a commit diff with tree-sitter and insert rows into mem_mrr_commits_code.

    Returns the number of rows inserted.
    """
    if not db.is_available():
        return 0

    project_id = db.get_or_create_project_id(project)
    guards = _read_yaml_guards(project)

    # Fetch commit metadata
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_COMMIT_META, (commit_hash, project_id))
                row = cur.fetchone()
        if not row:
            return 0
        commit_tags, _ = row
        commit_tags = commit_tags or {}
    except Exception as e:
        log.debug(f"extract_commit_code DB error: {e}")
        return 0

    # Guard: only process commits with user-set tags
    if guards["only_on_commits_with_tags"]:
        user_tag_keys = {"phase", "feature", "bug", "work-item"}
        if not any(k in commit_tags for k in user_tag_keys):
            return 0

    # Resolve code_dir
    code_dir: str = settings.code_dir or ""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_CODE_DIR, (project_id,))
                prow = cur.fetchone()
                if prow and prow[0]:
                    code_dir = prow[0]
    except Exception:
        pass
    if not code_dir:
        return 0

    # Fetch diff via git show
    try:
        result = subprocess.run(
            ["git", "show", "--format=", "-p", commit_hash],
            cwd=code_dir, capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            return 0
        raw_diff = result.stdout
    except Exception as e:
        log.debug(f"extract_commit_code git show error: {e}")
        return 0

    if not raw_diff.strip():
        return 0

    # Split diff into per-file sections
    # Each section starts with "diff --git a/... b/..."
    file_sections = re.split(r"(?=^diff --git )", raw_diff, flags=re.MULTILINE)

    rows_to_insert: list[tuple] = []
    client_id = db.default_client_id()
    min_lines = guards["min_lines"]

    haiku_system = _prompts.content("commit_symbol") or (
        "You are a code analyst. Given a changed symbol (class/method/function) and its diff, "
        "write a 1-sentence summary of what changed and why. Be concise."
    )

    for section in file_sections:
        if not section.strip() or not section.startswith("diff --git"):
            continue

        file_info = _parse_diff_for_file(section)
        file_path = file_info["file_path"]
        if not file_path:
            continue

        file_ext = Path(file_path).suffix
        file_language = _detect_language(file_ext)
        file_change = file_info["file_change"]
        added_lines = file_info["added_lines"]
        removed_lines = file_info["removed_lines"]

        # For deleted files, skip symbol extraction
        if file_change == "deleted":
            continue

        # Get file content after commit for symbol extraction
        source = ""
        if file_language and file_change in ("added", "modified", "renamed"):
            try:
                gr = subprocess.run(
                    ["git", "show", f"{commit_hash}:{file_path}"],
                    cwd=code_dir, capture_output=True, text=True, timeout=15,
                )
                if gr.returncode == 0:
                    source = gr.stdout
            except Exception:
                pass

        if not source or not file_language:
            continue

        symbols = _extract_symbols_from_source(source, file_language)
        diff_lines = section.splitlines()

        for sym in symbols:
            sym_start = sym["start_line"] + 1   # convert to 1-based
            sym_end = sym["end_line"] + 1
            sym_name = sym["name"]
            sym_type = sym["symbol_type"]
            sym_class = sym["class_name"]

            # Check which changed lines overlap with this symbol's range
            sym_added = {l for l in added_lines if sym_start <= l <= sym_end}
            sym_removed = {l for l in removed_lines if sym_start <= l <= sym_end}

            if not sym_added and not sym_removed:
                continue  # symbol not touched by this commit

            rows_added = len(sym_added)
            rows_removed = len(sym_removed)

            # Determine symbol_change type
            if sym_removed and not sym_added:
                symbol_change = "deleted"
            elif sym_added and not sym_removed:
                symbol_change = "added"
            else:
                symbol_change = "modified"

            # Extract diff snippet
            diff_snippet = _extract_diff_snippet(diff_lines, sym_start, sym_end)

            # LLM summary: skip if fewer than min_lines changed
            llm_summary: str | None = None
            if rows_added + rows_removed >= min_lines:
                symbol_label = f"{sym_class}.{sym_name}" if sym_class else sym_name
                llm_summary = await _haiku(
                    haiku_system,
                    f"File: {file_path}\nSymbol: {sym_type} {symbol_label}\nDiff:\n{diff_snippet[:1000]}",
                )

            rows_to_insert.append((
                client_id,
                project_id,
                commit_hash,
                file_path,
                file_ext,
                file_language,
                file_change,
                sym_type,
                sym_class,
                sym_name,
                symbol_change,
                rows_added,
                rows_removed,
                diff_snippet or None,
                llm_summary,
            ))

    if not rows_to_insert:
        return 0

    # Bulk insert
    inserted = 0
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                for row_params in rows_to_insert:
                    try:
                        cur.execute(_SQL_UPSERT_CODE_ROW, row_params)
                        inserted += cur.rowcount
                    except Exception as e:
                        log.debug(f"extract_commit_code insert error: {e}")
        log.info(f"extract_commit_code: {inserted} symbols for {commit_hash[:8]} ({project})")
    except Exception as e:
        log.debug(f"extract_commit_code bulk insert error: {e}")

    return inserted
