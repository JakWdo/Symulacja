#!/bin/bash
# Setup Enhanced Monitoring dla Sight Platform
# Konfiguruje Cloud Monitoring, alerty, dashboardy i integrację z PagerDuty

set -euo pipefail

# Kolory dla outputu
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Sight Platform - Enhanced Monitoring Setup ===${NC}"

# Sprawdź czy jest ustawiony PROJECT_ID
if [ -z "${PROJECT_ID:-}" ]; then
    echo -e "${RED}Error: PROJECT_ID environment variable is not set${NC}"
    echo "Usage: PROJECT_ID=your-gcp-project ./setup_enhanced_monitoring.sh"
    exit 1
fi

echo -e "${GREEN}Project ID: ${PROJECT_ID}${NC}"

# Sprawdź czy gcloud jest zalogowany
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
    echo -e "${RED}Error: Not authenticated with gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Ustaw projekt
gcloud config set project "${PROJECT_ID}"

echo -e "${YELLOW}Step 1/6: Enabling required APIs...${NC}"
gcloud services enable \
    monitoring.googleapis.com \
    cloudmonitoring.googleapis.com \
    logging.googleapis.com \
    billing.googleapis.com \
    --project="${PROJECT_ID}"

echo -e "${GREEN}✓ APIs enabled${NC}"

echo -e "${YELLOW}Step 2/6: Creating notification channels...${NC}"

# Email notification channel
EMAIL="${ALERT_EMAIL:-engineering@sight.com}"
echo "Creating email notification channel: ${EMAIL}"
EMAIL_CHANNEL_ID=$(gcloud alpha monitoring channels create \
    --display-name="Engineering Team Email" \
    --type=email \
    --channel-labels=email_address="${EMAIL}" \
    --format="value(name)" \
    --project="${PROJECT_ID}" 2>/dev/null || echo "")

if [ -z "${EMAIL_CHANNEL_ID}" ]; then
    echo -e "${YELLOW}Email channel already exists or creation failed, skipping...${NC}"
    # Try to find existing
    EMAIL_CHANNEL_ID=$(gcloud alpha monitoring channels list \
        --filter="displayName:'Engineering Team Email'" \
        --format="value(name)" \
        --project="${PROJECT_ID}" | head -1)
fi

echo -e "${GREEN}✓ Email channel: ${EMAIL_CHANNEL_ID}${NC}"

# Slack notification channel (optional)
if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    echo "Creating Slack notification channel..."
    SLACK_CHANNEL_ID=$(gcloud alpha monitoring channels create \
        --display-name="Slack Alerts" \
        --type=slack \
        --channel-labels=url="${SLACK_WEBHOOK_URL}" \
        --format="value(name)" \
        --project="${PROJECT_ID}" 2>/dev/null || echo "")

    if [ -n "${SLACK_CHANNEL_ID}" ]; then
        echo -e "${GREEN}✓ Slack channel: ${SLACK_CHANNEL_ID}${NC}"
    fi
fi

# PagerDuty notification channel (optional)
if [ -n "${PAGERDUTY_INTEGRATION_KEY:-}" ]; then
    echo "Creating PagerDuty notification channel..."
    PAGERDUTY_CHANNEL_ID=$(gcloud alpha monitoring channels create \
        --display-name="PagerDuty Incidents" \
        --type=pagerduty \
        --channel-labels=service_key="${PAGERDUTY_INTEGRATION_KEY}" \
        --format="value(name)" \
        --project="${PROJECT_ID}" 2>/dev/null || echo "")

    if [ -n "${PAGERDUTY_CHANNEL_ID}" ]; then
        echo -e "${GREEN}✓ PagerDuty channel: ${PAGERDUTY_CHANNEL_ID}${NC}"
    fi
fi

echo -e "${YELLOW}Step 3/6: Creating monitoring dashboard...${NC}"

# Replace PROJECT_ID in dashboard.json
DASHBOARD_JSON=$(cat monitoring/dashboard.json | sed "s/\${PROJECT_ID}/${PROJECT_ID}/g")

# Create dashboard
DASHBOARD_ID=$(gcloud monitoring dashboards create \
    --config-from-file=<(echo "${DASHBOARD_JSON}") \
    --format="value(name)" \
    --project="${PROJECT_ID}" 2>/dev/null || echo "")

if [ -z "${DASHBOARD_ID}" ]; then
    echo -e "${YELLOW}Dashboard creation failed or already exists${NC}"
else
    echo -e "${GREEN}✓ Dashboard created: ${DASHBOARD_ID}${NC}"
    echo -e "${GREEN}  View at: https://console.cloud.google.com/monitoring/dashboards/custom/${DASHBOARD_ID}?project=${PROJECT_ID}${NC}"
fi

echo -e "${YELLOW}Step 4/6: Creating alert policies...${NC}"

# Function to create alert policy from condition
create_alert_policy() {
    local display_name="$1"
    local filter="$2"
    local threshold="$3"
    local duration="$4"
    local comparison="${5:-COMPARISON_GT}"
    local aligner="${6:-ALIGN_RATE}"

    echo "Creating alert: ${display_name}"

    gcloud alpha monitoring policies create \
        --notification-channels="${EMAIL_CHANNEL_ID}" \
        --display-name="${display_name}" \
        --condition-display-name="${display_name}" \
        --condition-threshold-value="${threshold}" \
        --condition-threshold-duration="${duration}" \
        --condition-threshold-filter="${filter}" \
        --condition-threshold-comparison="${comparison}" \
        --condition-threshold-aggregations="alignment_period=60s,per_series_aligner=${aligner}" \
        --combiner="OR" \
        --project="${PROJECT_ID}" 2>/dev/null || echo "  ⚠ Alert already exists or creation failed"
}

# Critical alerts
create_alert_policy \
    "🚨 CRITICAL: High Error Rate >5%" \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="sight-api" AND metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"' \
    "0.05" \
    "120s" \
    "COMPARISON_GT" \
    "ALIGN_RATE"

create_alert_policy \
    "🚨 CRITICAL: Service Downtime" \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="sight-api" AND metric.type="run.googleapis.com/request_count" AND metric.label.response_code="200"' \
    "1" \
    "60s" \
    "COMPARISON_LT" \
    "ALIGN_RATE"

# High priority alerts
create_alert_policy \
    "⚠️ HIGH: API Latency p99 >2s" \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="sight-api" AND metric.type="run.googleapis.com/request_latencies"' \
    "2000" \
    "300s" \
    "COMPARISON_GT" \
    "ALIGN_PERCENTILE_99"

create_alert_policy \
    "⚠️ HIGH: API Latency p90 >500ms" \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="sight-api" AND metric.type="run.googleapis.com/request_latencies"' \
    "500" \
    "600s" \
    "COMPARISON_GT" \
    "ALIGN_PERCENTILE_90"

# Medium priority alerts
create_alert_policy \
    "📊 MEDIUM: High Memory Usage >85%" \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="sight-api" AND metric.type="run.googleapis.com/container/memory/utilizations"' \
    "0.85" \
    "300s" \
    "COMPARISON_GT" \
    "ALIGN_PERCENTILE_95"

create_alert_policy \
    "📊 MEDIUM: High CPU Usage >90%" \
    'resource.type="cloud_run_revision" AND resource.labels.service_name="sight-api" AND metric.type="run.googleapis.com/container/cpu/utilizations"' \
    "0.9" \
    "600s" \
    "COMPARISON_GT" \
    "ALIGN_PERCENTILE_99"

echo -e "${GREEN}✓ Alert policies created${NC}"

echo -e "${YELLOW}Step 5/6: Setting up custom metrics for application monitoring...${NC}"

cat <<EOF > /tmp/custom_metrics_descriptor.json
{
  "type": "custom.googleapis.com/sight/personas_generated_per_hour",
  "displayName": "Personas Generated per Hour",
  "description": "Number of AI personas generated per hour",
  "metricKind": "GAUGE",
  "valueType": "INT64",
  "unit": "personas/hour",
  "labels": [
    {
      "key": "project_id",
      "valueType": "STRING",
      "description": "User project ID"
    }
  ]
}
EOF

gcloud logging metrics create personas_generated_per_hour \
    --description="Personas generated per hour" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.operation="persona_generation" AND jsonPayload.status="success"' \
    --value-extractor='EXTRACT(jsonPayload.num_personas)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    --project="${PROJECT_ID}" 2>/dev/null || echo "  ⚠ Metric already exists"

gcloud logging metrics create tokens_per_minute \
    --description="LLM tokens consumed per minute" \
    --log-filter='resource.type="cloud_run_revision" AND jsonPayload.llm_usage.total_tokens>0' \
    --value-extractor='EXTRACT(jsonPayload.llm_usage.total_tokens)' \
    --metric-kind=DELTA \
    --value-type=INT64 \
    --project="${PROJECT_ID}" 2>/dev/null || echo "  ⚠ Metric already exists"

echo -e "${GREEN}✓ Custom metrics configured${NC}"

echo -e "${YELLOW}Step 6/6: Creating weekly report Cloud Function...${NC}"

# Create a simple Cloud Function for weekly reports (placeholder)
echo "#!/usr/bin/env python3
import datetime
from google.cloud import monitoring_v3

def send_weekly_report(request):
    \"\"\"Send weekly monitoring report via email\"\"\"
    # TODO: Implement weekly report generation
    # - Query monitoring metrics for last 7 days
    # - Calculate MTTR, incident count, top alerts
    # - Send email with summary
    return {'status': 'ok'}
" > /tmp/weekly_report.py

echo -e "${GREEN}✓ Weekly report function created (manual deployment needed)${NC}"

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. View dashboard: https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
echo "2. View alerts: https://console.cloud.google.com/monitoring/alerting?project=${PROJECT_ID}"
echo "3. Configure PagerDuty integration manually (if not done)"
echo "4. Set up weekly email reports"
echo "5. Test alerts with synthetic errors"
echo ""
echo -e "${YELLOW}Environment variables used:${NC}"
echo "  PROJECT_ID: ${PROJECT_ID}"
echo "  ALERT_EMAIL: ${EMAIL}"
echo "  SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL:-not set}"
echo "  PAGERDUTY_INTEGRATION_KEY: ${PAGERDUTY_INTEGRATION_KEY:-not set}"
echo ""
echo -e "${GREEN}MTTR Target: <20 minutes for P0 incidents${NC}"
