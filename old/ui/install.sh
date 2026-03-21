#!/usr/bin/env bash
# install.sh — One-time setup for aicli UI
# Usage: bash ui/install.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AICLI_DIR="$(dirname "$SCRIPT_DIR")"
UI_DIR="$SCRIPT_DIR"
CONFIG_DIR="$HOME/.aicli"
CONFIG_FILE="$CONFIG_DIR/config.json"

echo "=== aicli installer ==="
echo "UI dir:    $UI_DIR"
echo "aicli dir: $AICLI_DIR"
echo ""

# ── 1. macOS: Homebrew ──────────────────────────────────────────────────────
if [[ "$(uname)" == "Darwin" ]]; then
    if ! command -v brew &>/dev/null; then
        echo "→ Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        echo "✓ Homebrew found"
    fi
fi

# ── 2. Git ──────────────────────────────────────────────────────────────────
if ! command -v git &>/dev/null; then
    echo "→ Installing git..."
    if command -v brew &>/dev/null; then
        brew install git
    else
        echo "ERROR: git not found and cannot auto-install. Please install git manually." >&2
        exit 1
    fi
else
    echo "✓ git $(git --version | awk '{print $3}')"
fi

# ── 3. Node.js 20+ ──────────────────────────────────────────────────────────
NODE_OK=false
if command -v node &>/dev/null; then
    NODE_VER=$(node --version | sed 's/v//' | cut -d. -f1)
    if [[ "$NODE_VER" -ge 20 ]]; then
        NODE_OK=true
        echo "✓ Node.js $(node --version)"
    fi
fi

if [[ "$NODE_OK" == "false" ]]; then
    echo "→ Installing Node.js 20..."
    if command -v brew &>/dev/null; then
        brew install node
    elif command -v nvm &>/dev/null || [[ -f "$HOME/.nvm/nvm.sh" ]]; then
        # shellcheck disable=SC1090
        source "$HOME/.nvm/nvm.sh" 2>/dev/null || true
        nvm install 20
        nvm use 20
    else
        echo "→ Installing nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
        # shellcheck disable=SC1090
        source "$HOME/.nvm/nvm.sh"
        nvm install 20
        nvm use 20
    fi
fi

# ── 4. Python 3.12 ──────────────────────────────────────────────────────────
if ! command -v python3.12 &>/dev/null; then
    echo "→ Installing Python 3.12..."
    if command -v brew &>/dev/null; then
        brew install python@3.12
    else
        echo "ERROR: python3.12 not found. Install from https://python.org" >&2
        exit 1
    fi
else
    echo "✓ $(python3.12 --version)"
fi

# ── 5. Python dependencies ──────────────────────────────────────────────────
echo "→ Installing Python packages..."
python3.12 -m pip install -r "$UI_DIR/backend/requirements.txt" --quiet

# ── 6. Node dependencies ────────────────────────────────────────────────────
if [[ -f "$UI_DIR/package.json" ]]; then
    echo "→ Installing Node packages..."
    cd "$UI_DIR" && npm install --quiet
fi

# ── 7. Config file ──────────────────────────────────────────────────────────
mkdir -p "$CONFIG_DIR"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "✓ Config already exists: $CONFIG_FILE"
else
    # Prompt for workspace directory
    DEFAULT_WORKSPACE="$AICLI_DIR/workspace"
    echo ""
    read -rp "Workspace directory [$DEFAULT_WORKSPACE]: " WORKSPACE_DIR
    WORKSPACE_DIR="${WORKSPACE_DIR:-$DEFAULT_WORKSPACE}"

    INSTALLED_AT=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
    cat > "$CONFIG_FILE" <<EOF
{
  "workspace_dir": "$WORKSPACE_DIR",
  "aicli_dir": "$AICLI_DIR",
  "version": "2.0.0",
  "installed_at": "$INSTALLED_AT"
}
EOF
    echo "✓ Config written: $CONFIG_FILE"
fi

# ── 8. .env template ────────────────────────────────────────────────────────
ENV_FILE="$UI_DIR/backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    cat > "$ENV_FILE" <<'EOF'
# aicli backend environment
DATABASE_URL=
SECRET_KEY=change-me-run-openssl-rand-hex-32
DEV_MODE=true
# Set REQUIRE_AUTH=true for production
REQUIRE_AUTH=false
EOF
    echo "✓ .env template created: $ENV_FILE"
    echo "  → Set DATABASE_URL=postgresql://... for PostgreSQL support"
else
    echo "✓ .env already exists"
fi

echo ""
echo "=== Install complete ==="
echo "Run: bash ui/start.sh"
