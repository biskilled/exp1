#!/usr/bin/env bash
# Start the aicli backend server.
# Run this once — keep the terminal open, or use: bash start_backend.sh &

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Kill any stale process on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null
sleep 1

echo "Starting aicli backend..."
exec python3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000
