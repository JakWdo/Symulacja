#!/bin/bash
# Setup Google Cloud Monitoring Alerts dla Workflow Builder
# Usage: ./scripts/setup_monitoring_alerts.sh

set -e

PROJECT_ID="gen-lang-client-0508446677"
ALERTS_FILE="monitoring/alerts.yaml"

echo "🚀 Setting up Cloud Monitoring Alerts"
echo "   Project: $PROJECT_ID"
echo "   Alerts file: $ALERTS_FILE"
echo ""

# Check if alerts file exists
if [ ! -f "$ALERTS_FILE" ]; then
    echo "❌ Error: Alerts file not found: $ALERTS_FILE"
    exit 1
fi

echo "📝 Deploying alerts..."
echo ""

# Deploy alerts
if gcloud alpha monitoring policies create \
    --policy-from-file=$ALERTS_FILE \
    --project=$PROJECT_ID 2>&1 | tee /tmp/alert_output.txt; then
    echo ""
    echo "✅ Alerts deployed successfully!"
else
    # Check if error is due to existing policy
    if grep -q "already exists" /tmp/alert_output.txt; then
        echo ""
        echo "⚠️  Alert policy already exists. To update, first delete old policy:"
        echo "   gcloud alpha monitoring policies list --project=$PROJECT_ID"
        echo "   gcloud alpha monitoring policies delete POLICY_NAME --project=$PROJECT_ID"
        echo "   Then re-run this script."
    else
        echo ""
        echo "❌ Failed to deploy alerts. Check output above."
        exit 1
    fi
fi

echo ""
echo "📊 Listing alert policies:"
gcloud alpha monitoring policies list \
    --project=$PROJECT_ID \
    --filter="displayName~'Workflow'"

echo ""
echo "🎉 Monitoring setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure notification channels:"
echo "   https://console.cloud.google.com/monitoring/alerting/notifications?project=$PROJECT_ID"
echo "2. Test alerts by triggering failures"
echo "3. Monitor dashboard:"
echo "   https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"

rm -f /tmp/alert_output.txt
