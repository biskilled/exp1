#!/usr/bin/env bash
# PostToolUse hook — auto-format after Claude writes/edits a file.
# Receives JSON on stdin: { "tool_name": "Write", "tool_input": { "file_path": "..." } }

FILE_PATH=$(cat | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)

if [ -z "$FILE_PATH" ] || [ ! -f "$FILE_PATH" ]; then
    exit 0
fi

EXT="${FILE_PATH##*.}"

case "$EXT" in
  js|jsx|ts|tsx|css|scss|json|md)
    if command -v prettier &>/dev/null; then
      prettier --write "$FILE_PATH" --log-level warn
    fi
    ;;
  py)
    if command -v ruff &>/dev/null; then
      ruff format "$FILE_PATH" --quiet
    fi
    ;;
esac

exit 0
