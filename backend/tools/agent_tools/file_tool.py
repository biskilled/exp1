"""
file_tool.py — Agent-callable file system tools.

Provides tool definitions (Claude tool_use format) and handlers
for reading, writing, and listing files.
"""
from __future__ import annotations

from pathlib import Path


# ── Tool definitions ──────────────────────────────────────────────────────────

FILE_TOOL_DEFS: list[dict] = [
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
                "max_chars": {"type": "integer", "description": "Max characters to return (default 8000)"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file, creating parent directories as needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute or relative file path"},
                "content": {"type": "string", "description": "File content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_dir",
        "description": "List files and directories at a path.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to list"},
                "pattern": {"type": "string", "description": "Glob pattern (default: *)"},
            },
            "required": ["path"],
        },
    },
]


# ── Handlers ──────────────────────────────────────────────────────────────────

def handle_read_file(args: dict) -> str:
    p = Path(args["path"])
    if not p.exists():
        return f"Error: file not found: {p}"
    max_chars = int(args.get("max_chars", 8000))
    text = p.read_text(errors="replace")
    if len(text) > max_chars:
        text = text[:max_chars] + f"\n[...truncated at {max_chars} chars]"
    return text


def handle_write_file(args: dict) -> str:
    p = Path(args["path"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args["content"])
    return f"Written: {p} ({len(args['content'])} chars)"


def handle_list_dir(args: dict) -> str:
    p = Path(args["path"])
    if not p.exists():
        return f"Error: path not found: {p}"
    pattern = args.get("pattern", "*")
    entries = sorted(p.glob(pattern))
    lines = [
        f"{'d' if e.is_dir() else 'f'}  {e.name}"
        for e in entries
    ]
    return "\n".join(lines) if lines else "(empty)"


FILE_HANDLERS: dict = {
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "list_dir": handle_list_dir,
}
