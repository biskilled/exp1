#!/usr/bin/env bash
# post_push hook — triggers an AWS CodePipeline deployment.
# Requires: aws CLI configured + AWS_PIPELINE_NAME in .env (or aicli.yaml env)

if ! command -v aws &>/dev/null; then
    echo "aws CLI not found — skipping deploy"
    exit 0
fi

PIPELINE="${AWS_PIPELINE_NAME:-}"
if [ -z "$PIPELINE" ]; then
    echo "AWS_PIPELINE_NAME not set — skipping deploy"
    exit 0
fi

echo "Starting AWS pipeline: $PIPELINE"
aws codepipeline start-pipeline-execution --name "$PIPELINE"

if [ $? -eq 0 ]; then
    echo "AWS pipeline started"
else
    echo "AWS pipeline trigger failed" >&2
    exit 1
fi
