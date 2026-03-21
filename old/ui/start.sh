#!/usr/bin/env bash
# start.sh — Start the aicli backend server
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/backend"  # new location: aicli/backend/

cd "$BACKEND_DIR"
echo "Starting aicli backend at http://localhost:8000"
python3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
echo "Backend running: http://localhost:8000"
echo "PID: $!"
