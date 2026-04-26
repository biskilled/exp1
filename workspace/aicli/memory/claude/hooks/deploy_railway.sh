#!/usr/bin/env bash
# post_push hook — deploys to Railway after a successful push.
# Requires: railway CLI installed + RAILWAY_TOKEN in .env

if ! command -v railway &>/dev/null; then
    echo "railway CLI not found — skipping deploy"
    exit 0
fi

if [ -z "$RAILWAY_TOKEN" ]; then
    echo "RAILWAY_TOKEN not set — skipping deploy"
    exit 0
fi

echo "Deploying to Railway (branch: $AICLI_BRANCH)..."
RAILWAY_TOKEN="$RAILWAY_TOKEN" railway up --detach

if [ $? -eq 0 ]; then
    echo "Railway deploy triggered"
else
    echo "Railway deploy failed" >&2
    exit 1
fi
