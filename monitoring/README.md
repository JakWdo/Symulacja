# Enhanced Monitoring - Sight Platform

Kompleksowy system monitoringu produkcyjnego z Cloud Monitoring, alertami i integracją z PagerDuty.

## 📊 Komponenty

### 1. Alerty (`alerts_enhanced.yaml`)

12 alertów w 4 kategoriach priorytetów:

**🚨 CRITICAL (P0) - MTTR <20min:**
- High Error Rate >5%
- Service Downtime >1min
- Database Connection Failures

**⚠️ HIGH (P1) - MTTR <1hr:**
- API Latency p99 >2s
- API Latency p90 >500ms
- Daily Cost Spike >$100
- Gemini API Rate Limit

**📊 MEDIUM (P2):**
- High Memory Usage >85%
- High CPU Usage >90%
- Low Persona Generation Rate
- High Token Usage Rate

**ℹ️ LOW (P3):**
- Increased Cold Start Rate

### 2. Dashboard (`dashboard.json`)

Production dashboard z 11 widżetami:
- API Request Rate
- API Latency (p50, p90, p99)
- Error Rate z threshold 5%
- Active Users (24h)
- Memory & CPU Usage
- Daily Costs
- Personas Generated (per hour)
- Token Usage (per minute)
- Database Connection Pool
- Custom metrics

### 3. PagerDuty Integration (`pagerduty_integration.yaml`)

- Automatyczna eskalacja incydentów P0/P1
- Notification urgency mapping
- Escalation policy (3 poziomy)
- MTTR targets per priority
- Runbook links
- Weekly incident reports

### 4. Setup Script (`../scripts/setup_enhanced_monitoring.sh`)

Automatyczny deployment:
- Włączenie GCP APIs
- Utworzenie notification channels (Email, Slack, PagerDuty)
- Deploy dashboardu
- Utworzenie alert policies
- Konfiguracja custom metrics
- Setup weekly reports

## 🚀 Quick Start

### Wymagania

1. **GCP Project** z włączonymi API:
   - Cloud Monitoring
   - Cloud Logging
   - Billing API

2. **Credentials:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Environment Variables:**
   ```bash
   export PROJECT_ID="your-gcp-project"
   export ALERT_EMAIL="engineering@yourcompany.com"
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."  # Optional
   export PAGERDUTY_INTEGRATION_KEY="your-pagerduty-key"  # Optional
   ```

### Deployment

```bash
# 1. Run setup script
cd /path/to/Symulacja
./scripts/setup_enhanced_monitoring.sh

# 2. Verify dashboard created
gcloud monitoring dashboards list --project="${PROJECT_ID}"

# 3. Verify alerts created
gcloud alpha monitoring policies list --project="${PROJECT_ID}"

# 4. Test alert (generate synthetic error)
curl -X POST https://your-service.run.app/api/test-error
```

## 📈 Metrics Tracked

### Built-in Cloud Run Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `request_count` | Requests per second | - |
| `request_latencies` | API latency | p90: 500ms, p99: 2s |
| `container/memory/utilizations` | Memory usage % | 85% |
| `container/cpu/utilizations` | CPU usage % | 90% |
| `instance_count` | Active instances | - |

### Custom Application Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `personas_generated_per_hour` | Persona generation rate | <10/hr (degradation) |
| `tokens_per_minute` | LLM token consumption | >50k/min (cost spike) |
| `active_users` | Daily active users | - |
| `database_connection_error` | DB connection failures | >5/min |
| `gemini_rate_limit_error` | Gemini API rate limits | >10/5min |

### Billing Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|----------------|
| `billing.googleapis.com/project/cost` | Daily project cost | >$100/day |

## 🔔 Alert Notification Flow

```
GCP Alert Triggered
    ↓
Priority Mapping (P0/P1/P2/P3)
    ↓
Notification Channel Selection
    ├── P0: PagerDuty (SMS + Phone) + Slack + Email
    ├── P1: PagerDuty (Push) + Slack + Email
    ├── P2: Email + Slack
    └── P3: Slack only
    ↓
Escalation (if not acknowledged)
    ├── 0 min: Primary on-call
    ├── 20 min: Secondary on-call
    └── 60 min: Tech lead
```

## 📱 PagerDuty Setup

### 1. Create PagerDuty Service

1. Go to PagerDuty → Services → New Service
2. Name: "Sight Platform - Production"
3. Escalation Policy: Create "sight-platform-escalation"
4. Integration: "Events API v2"
5. Copy Integration Key

### 2. Configure Integration Key

```bash
# Set as environment variable
export PAGERDUTY_INTEGRATION_KEY="your-key-here"

# Or add to Cloud Run secret
gcloud secrets create pagerduty-integration-key \
    --data-file=<(echo -n "${PAGERDUTY_INTEGRATION_KEY}") \
    --project="${PROJECT_ID}"
```

### 3. Create Notification Channel in GCP

```bash
gcloud alpha monitoring channels create \
    --display-name="PagerDuty Incidents" \
    --type=pagerduty \
    --channel-labels=service_key="${PAGERDUTY_INTEGRATION_KEY}" \
    --project="${PROJECT_ID}"
```

### 4. Test Integration

```bash
# Send test incident
curl -X POST "https://events.pagerduty.com/v2/enqueue" \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "'"${PAGERDUTY_INTEGRATION_KEY}"'",
    "event_action": "trigger",
    "payload": {
      "summary": "Test alert from Sight Platform",
      "severity": "error",
      "source": "gcp-monitoring"
    }
  }'
```

## 📊 Viewing Dashboards

### Cloud Monitoring Dashboard

```bash
# List dashboards
gcloud monitoring dashboards list --project="${PROJECT_ID}"

# Get dashboard URL
echo "https://console.cloud.google.com/monitoring/dashboards?project=${PROJECT_ID}"
```

### Key Dashboard Views

1. **Overview** - Request rate, latency, errors, users
2. **Performance** - p50/p90/p99 latencies, memory, CPU
3. **Costs** - Daily costs, token usage, billing trends
4. **Application** - Personas/hour, focus groups, surveys

## 🔍 Troubleshooting

### Alert Not Firing

1. **Check filter:**
   ```bash
   # Test metric query in Logs Explorer
   gcloud logging read "resource.type=cloud_run_revision" --limit 10
   ```

2. **Verify threshold:**
   ```bash
   # Check current metric value
   gcloud monitoring time-series list \
       --filter='metric.type="run.googleapis.com/request_count"' \
       --project="${PROJECT_ID}"
   ```

3. **Check notification channels:**
   ```bash
   gcloud alpha monitoring channels list --project="${PROJECT_ID}"
   ```

### High False Positive Rate

1. **Adjust thresholds** in `alerts_enhanced.yaml`
2. **Increase duration** (e.g., 120s → 300s)
3. **Change aligner** (e.g., ALIGN_MEAN → ALIGN_PERCENTILE_95)

### Missing Custom Metrics

1. **Verify logging:**
   ```bash
   # Check if application logs contain required fields
   gcloud logging read 'jsonPayload.operation="persona_generation"' --limit 5
   ```

2. **Create log-based metric:**
   ```bash
   gcloud logging metrics create test_metric \
       --log-filter='jsonPayload.operation="test"' \
       --value-extractor='EXTRACT(jsonPayload.count)'
   ```

## 📧 Weekly Reports

Weekly incident summary emails include:
- Total incidents by priority (P0/P1/P2/P3)
- MTTR by priority level
- Top 5 most frequent alerts
- Cost trends
- Performance trends (latency, error rate)
- Uptime percentage

**Setup:**
1. Deploy Cloud Function: `functions/weekly_report/`
2. Schedule with Cloud Scheduler (every Monday 9 AM)
3. Configure recipient email list

## 🎯 MTTR Targets

| Priority | Target MTTR | Notification Method |
|----------|-------------|---------------------|
| P0 | <20 min | SMS + Phone + Push + Email |
| P1 | <1 hour | Push + Email |
| P2 | <2 hours | Email |
| P3 | <24 hours | Email (next business day) |

## 📚 Additional Resources

- [GCP Monitoring Docs](https://cloud.google.com/monitoring/docs)
- [PagerDuty Integration](https://support.pagerduty.com/docs/google-cloud-monitoring)
- [Alerting Best Practices](https://cloud.google.com/monitoring/alerts/best-practices)
- [Custom Metrics Guide](https://cloud.google.com/monitoring/custom-metrics)
