#!/bin/bash

# ==============================================================================
# Configure Cloud Run Health Check & Automatic Rollback
# ==============================================================================
# Purpose: Setup health check endpoint and automatic rollback policy
# Requirements: gcloud CLI authenticated
# Usage: ./scripts/configure_cloud_run_health_check.sh [production|staging]
# ==============================================================================

set -e  # Exit on error

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# GCP Project
GCP_PROJECT="gen-lang-client-0508446677"
GCP_REGION="europe-central2"

# Environment (production or staging)
ENVIRONMENT="${1:-production}"

# Service names
if [ "$ENVIRONMENT" = "staging" ]; then
    SERVICE_NAME="sight-staging"
else
    SERVICE_NAME="sight"
fi

# Health check configuration
HEALTH_CHECK_PATH="/health"
HEALTH_CHECK_INTERVAL=10  # seconds
HEALTH_CHECK_TIMEOUT=3    # seconds
HEALTH_CHECK_FAILURE_THRESHOLD=3  # failures before unhealthy
HEALTH_CHECK_SUCCESS_THRESHOLD=1  # successes before healthy

# Rollback policy
ROLLBACK_5XX_THRESHOLD=5  # % of 5xx errors to trigger rollback
ROLLBACK_LATENCY_THRESHOLD=2000  # ms p95 latency to trigger rollback
ROLLBACK_WINDOW=120  # seconds window for monitoring

echo "=============================================================================="
echo "Cloud Run Health Check & Rollback Configuration"
echo "=============================================================================="
echo ""
echo "Environment: $ENVIRONMENT"
echo "Service: $SERVICE_NAME"
echo "Region: $GCP_REGION"
echo "Health endpoint: $HEALTH_CHECK_PATH"
echo ""
echo "Rollback triggers:"
echo "  - 5xx errors > ${ROLLBACK_5XX_THRESHOLD}% for ${ROLLBACK_WINDOW}s"
echo "  - P95 latency > ${ROLLBACK_LATENCY_THRESHOLD}ms for ${ROLLBACK_WINDOW}s"
echo ""
echo "=============================================================================="
echo ""

# ==============================================================================
# STEP 1: Configure Health Check
# ==============================================================================

echo "📋 Step 1: Configuring health check endpoint..."
echo ""

gcloud run services update "$SERVICE_NAME" \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --health-checks-path="$HEALTH_CHECK_PATH" \
  --health-checks-interval="${HEALTH_CHECK_INTERVAL}s" \
  --health-checks-timeout="${HEALTH_CHECK_TIMEOUT}s" \
  --health-checks-unhealthy-threshold="$HEALTH_CHECK_FAILURE_THRESHOLD" \
  --health-checks-healthy-threshold="$HEALTH_CHECK_SUCCESS_THRESHOLD" \
  --quiet

if [ $? -eq 0 ]; then
    echo "✅ Health check configured successfully!"
else
    echo "❌ Health check configuration failed"
    exit 1
fi

echo ""

# ==============================================================================
# STEP 2: Configure Automatic Rollback (via Revision Annotations)
# ==============================================================================

echo "📋 Step 2: Configuring automatic rollback policy..."
echo ""

# Cloud Run doesn't have native automatic rollback based on metrics YET
# We configure:
# 1. Health checks (done above)
# 2. Traffic splitting (gradual rollout)
# 3. Monitoring alerts (manual rollback trigger)

echo "⚠️  Note: Cloud Run automatic metric-based rollback requires manual setup:"
echo ""
echo "1. Health checks: ✅ Configured (above)"
echo "2. Traffic splitting: Configure gradual rollout manually:"
echo "   gcloud run services update-traffic $SERVICE_NAME \\"
echo "     --to-revisions=LATEST=10 \\"
echo "     --region=$GCP_REGION"
echo ""
echo "3. Monitoring alerts: Setup in Cloud Monitoring:"
echo "   - Alert on 5xx rate > ${ROLLBACK_5XX_THRESHOLD}%"
echo "   - Alert on P95 latency > ${ROLLBACK_LATENCY_THRESHOLD}ms"
echo "   - Action: Manual rollback or Cloud Function trigger"
echo ""

# ==============================================================================
# STEP 3: Verify Health Check
# ==============================================================================

echo "📋 Step 3: Verifying health check..."
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --project="$GCP_PROJECT" \
  --region="$GCP_REGION" \
  --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo "❌ Could not retrieve service URL"
    exit 1
fi

echo "Service URL: $SERVICE_URL"
echo "Health endpoint: $SERVICE_URL$HEALTH_CHECK_PATH"
echo ""

# Test health endpoint
echo "Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL$HEALTH_CHECK_PATH")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Health check endpoint responding (HTTP $HTTP_CODE)"
else
    echo "⚠️  Health check returned HTTP $HTTP_CODE (expected 200)"
    echo "   This may indicate service issues or initial startup"
fi

echo ""

# ==============================================================================
# STEP 4: Display Rollback Commands
# ==============================================================================

echo "=============================================================================="
echo "Manual Rollback Commands"
echo "=============================================================================="
echo ""
echo "If automatic rollback is needed, use these commands:"
echo ""
echo "# List revisions:"
echo "gcloud run revisions list \\"
echo "  --service=$SERVICE_NAME \\"
echo "  --region=$GCP_REGION \\"
echo "  --limit=5"
echo ""
echo "# Rollback to previous revision:"
echo "gcloud run services update-traffic $SERVICE_NAME \\"
echo "  --to-revisions=PREVIOUS=100 \\"
echo "  --region=$GCP_REGION"
echo ""
echo "# Rollback to specific revision:"
echo "gcloud run services update-traffic $SERVICE_NAME \\"
echo "  --to-revisions=REVISION_NAME=100 \\"
echo "  --region=$GCP_REGION"
echo ""
echo "# Gradual rollout (10% canary):"
echo "gcloud run services update-traffic $SERVICE_NAME \\"
echo "  --to-revisions=LATEST=10,PREVIOUS=90 \\"
echo "  --region=$GCP_REGION"
echo ""

# ==============================================================================
# STEP 5: Setup Monitoring Alerts (instructions only)
# ==============================================================================

echo "=============================================================================="
echo "Monitoring Setup (Next Steps)"
echo "=============================================================================="
echo ""
echo "To complete automatic rollback setup, create these alerts in Cloud Monitoring:"
echo ""
echo "1. High Error Rate Alert:"
echo "   - Metric: 'cloud_run_revision/request_count' (5xx codes)"
echo "   - Condition: 5xx rate > ${ROLLBACK_5XX_THRESHOLD}% for ${ROLLBACK_WINDOW}s"
echo "   - Action: Notification channel (Slack/Email) + manual rollback"
echo ""
echo "2. High Latency Alert:"
echo "   - Metric: 'cloud_run_revision/request_latencies' (p95)"
echo "   - Condition: p95 > ${ROLLBACK_LATENCY_THRESHOLD}ms for ${ROLLBACK_WINDOW}s"
echo "   - Action: Notification channel (Slack/Email) + manual rollback"
echo ""
echo "3. Health Check Failures:"
echo "   - Metric: 'cloud_run_revision/container/startup_latencies'"
echo "   - Condition: Startup failures > 3 in 5 minutes"
echo "   - Action: Notification channel (Slack/Email)"
echo ""
echo "Cloud Monitoring Console:"
echo "https://console.cloud.google.com/monitoring/alerting?project=$GCP_PROJECT"
echo ""

# ==============================================================================
# COMPLETION
# ==============================================================================

echo "=============================================================================="
echo "Configuration Complete!"
echo "=============================================================================="
echo ""
echo "✅ Health check configured: $HEALTH_CHECK_PATH"
echo "✅ Service updated: $SERVICE_NAME"
echo "✅ Rollback commands documented (see above)"
echo ""
echo "⚠️  Next steps:"
echo "   1. Setup monitoring alerts in Cloud Monitoring console"
echo "   2. Test health check: curl $SERVICE_URL$HEALTH_CHECK_PATH"
echo "   3. Test rollback procedure with staging environment first"
echo ""
echo "MTTR Goal: <2 minutes (manual rollback)"
echo "Automatic health check: Every ${HEALTH_CHECK_INTERVAL}s"
echo ""
echo "=============================================================================="
