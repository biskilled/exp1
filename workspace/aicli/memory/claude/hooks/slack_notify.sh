#!/usr/bin/env bash
# post_commit hook — sends a Slack notification.
# Requires SLACK_WEBHOOK env var (add to .env).

if [ -z "$SLACK_WEBHOOK" ]; then
    echo "SLACK_WEBHOOK not set — skipping notification"
    exit 0
fi

FEATURE="${AICLI_FEATURE:-none}"
TAG="${AICLI_TAG:-none}"
BRANCH="${AICLI_BRANCH:-unknown}"
HASH="${AICLI_COMMIT_HASH:0:8}"
MSG="${AICLI_COMMIT_MESSAGE}"

PAYLOAD=$(cat <<EOF
{
  "text": "🔧 *Commit* \`${HASH}\` on \`${BRANCH}\`",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*${MSG}*\n• Branch: \`${BRANCH}\`  Feature: \`${FEATURE}\`  Tag: \`#${TAG}\`"
      }
    }
  ]
}
EOF
)

curl -s -X POST "$SLACK_WEBHOOK" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" \
    -o /dev/null

echo "Slack notified"
