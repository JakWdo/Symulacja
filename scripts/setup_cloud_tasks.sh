#!/bin/bash
# Setup Cloud Tasks queue dla Workflow Builder
# Usage: ./scripts/setup_cloud_tasks.sh

set -e

PROJECT_ID="gen-lang-client-0508446677"
REGION="europe-central2"
QUEUE_NAME="workflow-executions"

echo "🚀 Setting up Cloud Tasks queue: $QUEUE_NAME"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Check if queue already exists
if gcloud tasks queues describe $QUEUE_NAME \
    --location=$REGION \
    --project=$PROJECT_ID &>/dev/null; then
    echo "✅ Queue already exists: $QUEUE_NAME"
    echo ""
    gcloud tasks queues describe $QUEUE_NAME \
        --location=$REGION \
        --project=$PROJECT_ID
else
    echo "📝 Creating queue: $QUEUE_NAME"
    gcloud tasks queues create $QUEUE_NAME \
        --location=$REGION \
        --max-dispatches-per-second=500 \
        --max-concurrent-dispatches=100 \
        --max-attempts=3 \
        --min-backoff=5s \
        --max-backoff=300s \
        --project=$PROJECT_ID

    echo ""
    echo "✅ Queue created successfully!"
    echo ""
    gcloud tasks queues describe $QUEUE_NAME \
        --location=$REGION \
        --project=$PROJECT_ID
fi

echo ""
echo "🎉 Cloud Tasks setup complete!"
echo ""
echo "Next steps:"
echo "1. Deploy backend: git push origin main"
echo "2. Verify queue: gcloud tasks queues describe $QUEUE_NAME --location=$REGION"
echo "3. Monitor tasks: gcloud tasks list --queue=$QUEUE_NAME --location=$REGION"
