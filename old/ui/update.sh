#!/usr/bin/env bash
# update.sh — Update aicli UI (git pull + reinstall deps)
# Workspace data is NEVER touched: workspace/, ui/backend/data/, aicli.yaml, ui/backend/.env
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AICLI_DIR="$(dirname "$SCRIPT_DIR")"
UI_DIR="$SCRIPT_DIR"
CONFIG_FILE="$HOME/.aicli/config.json"

echo "=== aicli updater ==="

# ── 1. Stop running backend ─────────────────────────────────────────────────
echo "→ Stopping backend (if running)..."
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# ── 2. Git pull ─────────────────────────────────────────────────────────────
echo "→ Pulling latest changes..."
git -C "$AICLI_DIR" pull --ff-only

# ── 3. Reinstall Python deps ────────────────────────────────────────────────
echo "→ Updating Python packages..."
python3.12 -m pip install -r "$UI_DIR/backend/requirements.txt" --quiet

# ── 4. Reinstall Node deps ──────────────────────────────────────────────────
if [[ -f "$UI_DIR/package.json" ]]; then
    echo "→ Updating Node packages..."
    cd "$UI_DIR" && npm install --quiet
fi

# ── 5. Update version in config ─────────────────────────────────────────────
if command -v python3.12 &>/dev/null && [[ -f "$CONFIG_FILE" ]]; then
    UPDATED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
    python3.12 - <<PYEOF
import json, sys
from pathlib import Path

cfg_path = Path("$CONFIG_FILE")
try:
    cfg = json.loads(cfg_path.read_text())
    cfg["updated_at"] = "$UPDATED_AT"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    print("✓ Config updated")
except Exception as e:
    print(f"  (config update skipped: {e})")
PYEOF
fi

echo ""
echo "=== Update complete ==="
echo "Preserved: workspace/, ui/backend/data/, aicli.yaml, ui/backend/.env"
echo "Run: bash ui/start.sh"
