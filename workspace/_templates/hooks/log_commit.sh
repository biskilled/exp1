#!/usr/bin/env bash
# post_commit hook — appends a CSV line to .aicli/commit_log.csv
# Available env vars: AICLI_COMMIT_HASH, AICLI_COMMIT_MESSAGE,
#   AICLI_FEATURE, AICLI_TAG, AICLI_BRANCH, AICLI_PROVIDER

LOG_FILE=".aicli/commit_log.csv"

# Write header if file doesn't exist
if [ ! -f "$LOG_FILE" ]; then
    echo "timestamp,hash,branch,feature,tag,provider,message" > "$LOG_FILE"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Escape commas in message
MSG="${AICLI_COMMIT_MESSAGE//,/;}"

echo "${TIMESTAMP},${AICLI_COMMIT_HASH:0:8},${AICLI_BRANCH},${AICLI_FEATURE},${AICLI_TAG},${AICLI_PROVIDER},\"${MSG}\"" \
    >> "$LOG_FILE"

echo "Logged commit to $LOG_FILE"
