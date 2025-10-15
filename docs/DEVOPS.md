# 🚀 DevOps & Infrastructure

Kompleksowa dokumentacja DevOps dla Market Research SaaS - od Docker architecture do CI/CD, monitoring i production deployment.

---

## 📋 Spis Treści

1. [Docker Architecture](#docker-architecture)
2. [CI/CD Pipeline](#cicd-pipeline)
3. [Monitoring & Observability](#monitoring--observability)
4. [Backup Strategy](#backup-strategy)
5. [Production Deployment](#production-deployment)
6. [Security Hardening](#security-hardening)
7. [Resource Management](#resource-management)
8. [Production Readiness Checklist](#production-readiness-checklist)
9. [Troubleshooting](#troubleshooting)

---

## 🐳 Docker Architecture

### Multi-Stage Builds

#### Backend (Dockerfile)

**2-stage build:**
1. **BUILDER** - instaluje gcc, g++, kompiluje Python packages
2. **RUNTIME** - kopiuje tylko packages, bez build tools

**Korzyści:**
- Image size: 850MB → 450MB (47% mniejszy)
- Security: brak compilerów w runtime
- Layer caching: requirements.txt cached osobno od kodu

**Dockerfile structure:**
```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim as runtime
COPY --from=builder /root/.local /root/.local
WORKDIR /app
COPY . .
USER appuser
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]
```

#### Frontend (frontend/Dockerfile)

**4-stage build:**
1. **DEPS** - `npm ci` (cached dopóki package.json nie zmieni się)
2. **BUILDER** - `npm run build` (production static files)
3. **DEVELOPMENT** - Vite dev server z hot reload
4. **PRODUCTION** - nginx serving static build

**Korzyści:**
- Instant starty: node_modules z cache (NIE npm install przy każdym up)
- Production: 500MB → 25MB (95% mniejszy!)
- Named volume `frontend_node_modules` zapobiega konfliktom host vs container

### Docker Compose

#### Development (docker-compose.yml)

**Key features:**
- Hot reload dla backendu (uvicorn --reload) i frontendu (Vite)
- Volume mounts: `./:/app` dla live code changes
- Named volume: `frontend_node_modules` (krytyczne dla uniknięcia konfliktów)
- Healthchecks: API startuje dopiero gdy databases są healthy
- Multi-stage targets: `target: runtime` (backend), `target: development` (frontend)

**WAŻNE:** Frontend NIE uruchamia `npm install` przy każdym `up` (jest w Dockerfile!)

**Example service (API):**
```yaml
api:
  build:
    context: .
    target: runtime
  volumes:
    - ./:/app
  environment:
    - DATABASE_URL=${DATABASE_URL}
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_started
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
    interval: 10s
    timeout: 5s
    retries: 3
```

#### Production (docker-compose.prod.yml)

**Key features:**
- Frontend: nginx serving static build
- Backend: gunicorn z multiple workers
- Resource limits (CPU, memory)
- Internal network: databases nie exposed na host
- BRAK volume mounts (kod z image)
- Environment variables z `.env.production`

### .dockerignore

#### Backend (.dockerignore)
Wyklucza: `__pycache__`, `.pytest_cache`, `.venv`, `frontend/`, `node_modules`, `.git`, `docs/`

**Korzyść:** Build context 500-800MB → 50-100MB (70-90% mniejszy)

#### Frontend (frontend/.dockerignore)
Wyklucza: `node_modules`, `dist`, `.env*`

### Named Volumes

#### Development
- `postgres_data`, `redis_data`, `neo4j_data` - Database persistence
- `api_static` - Avatary użytkowników
- `frontend_node_modules` - **KRYTYCZNE**: Zapobiega konfliktom host (macOS) vs container (Linux)

#### Production
- Wszystkie development volumes + `nginx_logs`
- Rozważ external volumes z backupami

### Performance Benchmarks

#### Build Times (cached)
- Backend: ~5-10s (tylko kod changed)
- Frontend: ~5-10s (tylko kod changed)
- Full rebuild (dependencies): ~60-120s

#### Image Sizes
- Backend: ~450MB (runtime stage) ⚠️ **TARGET: 450MB** ✅
- Frontend dev: ~500MB (node + deps)
- Frontend prod: ~25MB (nginx + static) ⚠️ **TARGET: 25MB** ✅

**Current vs Target (z audytu 2025-10-15):**
- Backend: **2.91GB** (actual) → **450MB** (target) = **6x too large** ❌
- Frontend: **690MB** (actual) → **25MB** (target) = **27x too large** ❌

**ACTION REQUIRED (Phase 3):** Optimize Dockerfile (remove unnecessary layers, better .dockerignore)

#### Runtime
- Backend cold start: ~5-10s (czeka na databases)
- Frontend cold start: ~1-2s (Vite dev server)
- Production frontend: <100ms (nginx static)

### Development Workflow

#### Podstawowe komendy

```bash
# Start all services
docker-compose up -d

# Rebuild (po zmianie requirements.txt / package.json)
docker-compose up --build -d

# Logi
docker-compose logs -f api
docker-compose logs -f frontend

# Stop
docker-compose down

# Czysty start (USUWA DANE!)
docker-compose down -v
docker-compose up --build -d
```

#### Kiedy rebuild?

✅ **REBUILD wymagany:**
- Zmiana `requirements.txt`
- Zmiana `package.json`
- Zmiana `Dockerfile`

❌ **REBUILD NIE wymagany:**
- Zmiana kodu `.py`, `.tsx` (hot reload działa)

---

## 🔄 CI/CD Pipeline

**Status:** ❌ **BRAK CI/CD** (DevOps Score: 4.8/10 - CRITICAL GAP)

**Problem:** 380 testów nie są automated, brak security scanning, manual deployment

**ACTION REQUIRED (Phase 1 - CRITICAL):** Implementacja GitHub Actions workflow

### Proposed GitHub Actions Workflow

#### CI Workflow (.github/workflows/ci.yml)

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  # Job 1: Unit & Integration Tests
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15

    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

      neo4j:
        image: neo4j:5-community
        env:
          NEO4J_AUTH: neo4j/test_password
        ports:
          - 7687:7687

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run unit tests (fast)
        run: |
          pytest tests/unit/ -v --cov=app --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: test_password

      - name: Run integration tests
        run: |
          pytest tests/integration/ -v
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USER: neo4j
          NEO4J_PASSWORD: test_password

      - name: Run E2E smoke test (CI-friendly, no external APIs)
        run: |
          pytest tests/e2e/test_e2e_ci_smoke.py -v
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_password@localhost:5432/test_db

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  # Job 2: Build Docker Images
  build:
    runs-on: ubuntu-latest
    needs: test
    timeout-minutes: 20

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub (or GitHub Container Registry)
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: .
          target: runtime
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/market-research-api:${{ github.sha }}
            ${{ secrets.DOCKER_USERNAME }}/market-research-api:latest
          cache-from: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/market-research-api:buildcache
          cache-to: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/market-research-api:buildcache,mode=max

      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          target: production
          push: true
          tags: |
            ${{ secrets.DOCKER_USERNAME }}/market-research-frontend:${{ github.sha }}
            ${{ secrets.DOCKER_USERNAME }}/market-research-frontend:latest
          cache-from: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/market-research-frontend:buildcache
          cache-to: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/market-research-frontend:buildcache,mode=max

  # Job 3: Security Scanning
  security:
    runs-on: ubuntu-latest
    needs: build
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner (Docker images)
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ secrets.DOCKER_USERNAME }}/market-research-api:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security tab
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Run pip-audit (Python dependencies)
        run: |
          pip install pip-audit
          pip-audit -r requirements.txt --desc
```

#### CD Workflow (.github/workflows/deploy.yml)

```yaml
name: Deploy to Production

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment }}
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to ${{ github.event.inputs.environment }}
        run: |
          echo "Deploying to ${{ github.event.inputs.environment }}..."
          # SSH to server + docker-compose pull + up -d
          # Or use Kubernetes helm upgrade
          # Or use Terraform apply

      - name: Health check
        run: |
          curl -f https://api.${{ github.event.inputs.environment }}.example.com/health/ready
```

### CI/CD Best Practices

1. **Fast Feedback** - Unit tests (<2 min), Integration tests (<5 min)
2. **Caching** - Docker layer caching, pip cache, npm cache
3. **Parallel Jobs** - Test + Build + Security scan równolegle
4. **Matrix Strategy** - Test na multiple Python versions (opcjonalnie)
5. **Branch Protection** - Require CI pass before merge
6. **Secrets Management** - GitHub Secrets dla API keys, passwords
7. **Deployment Approval** - Manual approval dla production

### Timeline

**Phase 1 (Week 1 - CRITICAL):**
- [ ] Setup GitHub Actions workflow (ci.yml) - 8h
- [ ] Configure secrets (DOCKER_USERNAME, API keys) - 1h
- [ ] Test CI pipeline (fix flaky tests) - 4h
- [ ] Setup branch protection rules - 1h
- [ ] Document CI/CD workflow - 2h

**Phase 2 (Week 2 - HIGH):**
- [ ] Add deployment workflow (cd.yml) - 6h
- [ ] Configure staging environment - 4h
- [ ] Test automated deployment - 2h
- [ ] Add smoke tests post-deployment - 2h

---

## 📊 Monitoring & Observability

**Status:** ❌ **BRAK MONITORING** (DevOps Score: 4.8/10 - CRITICAL GAP)

**Problem:** No visibility into production issues, no alerts, no metrics

**ACTION REQUIRED (Phase 1 - CRITICAL):** Prometheus + Grafana setup

### Prometheus + Grafana Stack

#### Architecture

```
┌─────────────────┐
│   Application   │
│   (FastAPI)     │
└────────┬────────┘
         │ /metrics endpoint
         ↓
┌─────────────────┐
│   Prometheus    │ ← Scrapes metrics every 15s
│   (Time Series  │
│    Database)    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│    Grafana      │ ← Visualizes metrics
│   (Dashboards)  │
└─────────────────┘
         │
         ↓
┌─────────────────┐
│   Alertmanager  │ ← Sends alerts (Slack, PagerDuty)
└─────────────────┘
```

#### Setup (docker-compose.monitoring.yml)

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
    ports:
      - "9090:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    ports:
      - "9093:9093"
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

#### Metrics to Track

**System Metrics:**
- CPU usage (per container)
- Memory usage (per container)
- Disk I/O (read/write)
- Network I/O (in/out)

**Application Metrics (FastAPI):**
```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# LLM metrics
llm_requests_total = Counter(
    'llm_requests_total',
    'Total LLM API calls',
    ['model', 'operation']
)

llm_tokens_used = Counter(
    'llm_tokens_used',
    'Total tokens used',
    ['model', 'operation']
)

llm_request_duration_seconds = Histogram(
    'llm_request_duration_seconds',
    'LLM request latency',
    ['model', 'operation']
)

# Database metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    ['database']
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query latency',
    ['query_type']
)

# Business metrics
personas_generated_total = Counter('personas_generated_total', 'Total personas generated')
focus_groups_completed_total = Counter('focus_groups_completed_total', 'Total focus groups completed')
surveys_completed_total = Counter('surveys_completed_total', 'Total surveys completed')
```

**Database Metrics:**
- PostgreSQL: connections, queries/sec, cache hit ratio
- Redis: hit rate, memory usage, connected clients
- Neo4j: query time, node count, relationship count

#### Grafana Dashboards

**1. System Overview Dashboard**
- CPU usage (all containers)
- Memory usage (all containers)
- Disk usage
- Network I/O

**2. Application Performance Dashboard**
- Request rate (requests/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Active users

**3. LLM Usage Dashboard**
- Token usage (per hour, per day)
- Cost tracking ($$ per operation)
- Model usage distribution (Flash vs Pro)
- Average latency per model

**4. Database Performance Dashboard**
- Query latency (p50, p95, p99)
- Connection pool usage
- Cache hit rate (Redis, PostgreSQL)
- Slow queries (>1s)

**5. Business Metrics Dashboard**
- Personas generated (per hour, per day)
- Focus groups completed
- Survey responses
- User activity

#### Alerting Rules

```yaml
# monitoring/alertmanager.yml
route:
  receiver: 'slack-notifications'
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 3h

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts'
        title: 'Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

# Alerts
groups:
  - name: production_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected (>5%)"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 5m
        annotations:
          summary: "High latency detected (p95 >2s)"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL is down"

      - alert: HighLLMCost
        expr: rate(llm_tokens_used[1h]) > 100000
        for: 10m
        annotations:
          summary: "High LLM token usage (>100k/hour)"
```

### Logging Stack (Opcjonalne - Phase 2)

#### Loki + Promtail (Lightweight)

```yaml
# docker-compose.monitoring.yml (extend)
loki:
  image: grafana/loki:latest
  ports:
    - "3100:3100"
  volumes:
    - loki_data:/loki

promtail:
  image: grafana/promtail:latest
  volumes:
    - /var/log:/var/log
    - /var/lib/docker/containers:/var/lib/docker/containers
    - ./monitoring/promtail.yml:/etc/promtail/promtail.yml
  command: -config.file=/etc/promtail/promtail.yml
```

**Korzyści:**
- Centralized logging (all containers)
- Log aggregation + search
- Integration z Grafana
- Retention policy (30 days)

### Timeline

**Phase 1 (Week 1-2 - CRITICAL):**
- [ ] Setup Prometheus + Grafana (docker-compose.monitoring.yml) - 8h
- [ ] Implement metrics in FastAPI (/metrics endpoint) - 6h
- [ ] Create 3 basic dashboards (System, App, Database) - 6h
- [ ] Configure alerting (Slack integration) - 4h
- [ ] Test alerts (trigger error conditions) - 2h

**Phase 2 (Week 3-4 - HIGH):**
- [ ] Add Loki + Promtail (log aggregation) - 6h
- [ ] Create 2 advanced dashboards (LLM Usage, Business Metrics) - 4h
- [ ] Configure advanced alerts (cost, performance) - 4h
- [ ] Document monitoring setup - 2h

---

## 💾 Backup Strategy

**Status:** ❌ **BRAK BACKUPS** (DevOps Score: 4.8/10 - CRITICAL GAP)

**Problem:** No automated backups, data loss risk w przypadku failure

**ACTION REQUIRED (Phase 1 - CRITICAL):** Automated daily backups z 30-day retention

### Backup Requirements

**RTO (Recovery Time Objective):** 4 hours (czas na przywrócenie systemu)
**RPO (Recovery Point Objective):** 24 hours (maksymalna utrata danych = daily backups)

### Databases to Backup

1. **PostgreSQL** - User data, projects, personas, focus groups, surveys
2. **Neo4j** - Graph data (RAG knowledge graph, focus group analysis)
3. **Redis** - Cache + session data (opcjonalnie - ephemeral)
4. **Static files** - User avatars (`data/avatars/`)

### Automated Backup Script

#### backup.sh

```bash
#!/bin/bash
# Automated backup script dla Market Research SaaS
# Usage: ./scripts/backup.sh

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
S3_BUCKET="s3://my-backups-bucket/market-research-saas"

echo "🔄 Starting backup process at $(date)"

# 1. PostgreSQL Backup
echo "📦 Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U market_research market_research_db \
  | gzip > "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"

# 2. Neo4j Backup
echo "📦 Backing up Neo4j..."
docker-compose exec -T neo4j neo4j-admin database dump neo4j \
  --to-path=/backups/neo4j_$TIMESTAMP.dump

# 3. Redis Backup (RDB snapshot)
echo "📦 Backing up Redis..."
docker-compose exec -T redis redis-cli SAVE
docker cp $(docker-compose ps -q redis):/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# 4. Static Files Backup (avatars)
echo "📦 Backing up static files..."
tar -czf "$BACKUP_DIR/static_$TIMESTAMP.tar.gz" data/avatars/

# 5. Upload to S3 (or other cloud storage)
echo "☁️  Uploading backups to S3..."
aws s3 sync "$BACKUP_DIR" "$S3_BUCKET" --exclude "*" --include "*$TIMESTAMP*"

# 6. Cleanup old backups (retention policy)
echo "🗑️  Cleaning up old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete

# 7. Verify backup integrity
echo "✅ Verifying backup integrity..."
for file in "$BACKUP_DIR"/*$TIMESTAMP*; do
  if [ -f "$file" ]; then
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
    if [ "$size" -gt 0 ]; then
      echo "✅ $file: $size bytes"
    else
      echo "❌ $file: FAILED (0 bytes)"
      exit 1
    fi
  fi
done

echo "✅ Backup completed successfully at $(date)"
```

### Backup Schedule (Cron)

```bash
# Add to crontab (crontab -e)
# Daily backup at 2 AM
0 2 * * * /path/to/scripts/backup.sh >> /var/log/backup.log 2>&1

# Weekly full backup (Sunday 3 AM)
0 3 * * 0 /path/to/scripts/backup_full.sh >> /var/log/backup_full.log 2>&1
```

### Backup Restoration Procedure

#### restore.sh

```bash
#!/bin/bash
# Restore from backup
# Usage: ./scripts/restore.sh <timestamp>

set -euo pipefail

TIMESTAMP=$1
BACKUP_DIR="/backups"

echo "🔄 Starting restore process for backup: $TIMESTAMP"

# 1. Stop services
echo "⏸️  Stopping services..."
docker-compose down

# 2. Restore PostgreSQL
echo "📦 Restoring PostgreSQL..."
gunzip < "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz" | \
  docker-compose exec -T postgres psql -U market_research market_research_db

# 3. Restore Neo4j
echo "📦 Restoring Neo4j..."
docker-compose exec -T neo4j neo4j-admin database load neo4j \
  --from-path=/backups/neo4j_$TIMESTAMP.dump --overwrite-destination=true

# 4. Restore Redis (RDB)
echo "📦 Restoring Redis..."
docker cp "$BACKUP_DIR/redis_$TIMESTAMP.rdb" \
  $(docker-compose ps -q redis):/data/dump.rdb
docker-compose restart redis

# 5. Restore Static Files
echo "📦 Restoring static files..."
tar -xzf "$BACKUP_DIR/static_$TIMESTAMP.tar.gz" -C data/

# 6. Start services
echo "▶️  Starting services..."
docker-compose up -d

echo "✅ Restore completed successfully"
```

### Backup Testing (Monthly Drill)

**Monthly Disaster Recovery Drill:**
1. Download latest backup from S3
2. Restore to staging environment
3. Verify data integrity (run smoke tests)
4. Document any issues

```bash
# Monthly DR drill script
./scripts/restore.sh <latest_timestamp> --environment staging
pytest tests/e2e/test_e2e_ci_smoke.py -v
```

### Timeline

**Phase 1 (Week 1 - CRITICAL):**
- [ ] Write backup script (backup.sh) - 3h
- [ ] Setup cron job (daily backups) - 1h
- [ ] Configure S3 bucket + IAM permissions - 2h
- [ ] Test backup + restoration procedure - 2h
- [ ] Document backup/restore process - 1h

**Phase 2 (Week 2-3 - HIGH):**
- [ ] Write restore script (restore.sh) - 2h
- [ ] Setup backup monitoring (alerts if backup fails) - 2h
- [ ] Perform first disaster recovery drill - 2h
- [ ] Document DR procedures - 1h

---

## 🚀 Production Deployment

### Pre-Deploy Checklist

**Security:**
- [ ] SECRET_KEY zmieniony (użyj `openssl rand -hex 32`)
- [ ] Hasła baz danych zmienione (POSTGRES_PASSWORD, NEO4J_PASSWORD)
- [ ] ALLOWED_ORIGINS skonfigurowany (tylko trusted domains, NIE `*`)
- [ ] DEBUG=false w production
- [ ] SSL/TLS certyfikaty skonfigurowane (Let's Encrypt)

**Infrastructure:**
- [ ] Backupy dla postgres_data, neo4j_data, api_static
- [ ] Monitoring/alerting skonfigurowany (Prometheus + Grafana)
- [ ] Firewall rules ustawione (tylko 80/443 exposed)
- [ ] CI/CD pipeline działa (automated testing + deployment)

**Performance:**
- [ ] Gunicorn workers dostosowane do CPU (2-4x cores)
- [ ] Database connection pools skonfigurowane (20-50 connections)
- [ ] Redis maxmemory policy ustawiony (allkeys-lru, 2GB)
- [ ] Neo4j memory limits dostosowane (heap: 2-4GB)

### Setup

#### 1. Skopiuj Production Template

```bash
cp .env.production.example .env.production
```

#### 2. Wypełnij Environment Variables

```bash
# .env.production
# === SECURITY (CRITICAL!) ===
SECRET_KEY=$(openssl rand -hex 32)  # CHANGE THIS!
POSTGRES_PASSWORD=$(openssl rand -base64 32)  # CHANGE THIS!
NEO4J_PASSWORD=$(openssl rand -base64 32)  # CHANGE THIS!
DEBUG=false
ENVIRONMENT=production

# === DATABASE ===
DATABASE_URL=postgresql+asyncpg://market_research:${POSTGRES_PASSWORD}@postgres:5432/market_research_db

# === GOOGLE GEMINI ===
GOOGLE_API_KEY=your_production_api_key  # REQUIRED!

# === REDIS & NEO4J ===
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j

# === CORS ===
ALLOWED_ORIGINS=https://app.example.com,https://www.example.com

# === GUNICORN (Production) ===
WORKERS=4  # 2-4x CPU cores
WORKER_CLASS=uvicorn.workers.UvicornWorker
TIMEOUT=120
KEEPALIVE=5
```

#### 3. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d --build

# Check status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api

# Run migrations
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head

# Initialize Neo4j indexes
docker-compose -f docker-compose.prod.yml exec api python scripts/init_neo4j_indexes.py
```

### Production docker-compose.prod.yml

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      target: runtime
    command: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - NEO4J_URI=${NEO4J_URI}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - ENVIRONMENT=production
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
    restart: unless-stopped
    networks:
      - internal
      - external
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      target: production
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/ssl:/etc/nginx/ssl:ro
    restart: unless-stopped
    networks:
      - external
    depends_on:
      api:
        condition: service_healthy

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=market_research
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=market_research_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
    restart: unless-stopped
    networks:
      - internal
    # NO PORTS EXPOSED (internal network only)

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
    restart: unless-stopped
    networks:
      - internal

  neo4j:
    image: neo4j:5-community
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_server_memory_heap_initial__size=2G
      - NEO4J_server_memory_heap_max__size=4G
    volumes:
      - neo4j_data:/data
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    restart: unless-stopped
    networks:
      - internal

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  api_static:

networks:
  internal:
    driver: bridge
  external:
    driver: bridge
```

### SSL/TLS Setup (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d app.example.com -d www.example.com

# Auto-renewal (cron)
0 0 * * * certbot renew --quiet
```

### Health Check Endpoints

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/live")
async def liveness():
    """Liveness probe - is the app running?"""
    return {"status": "ok"}

@router.get("/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe - is the app ready to serve traffic?"""
    try:
        # Check database connection
        await db.execute("SELECT 1")
        return {"status": "ready", "database": "ok"}
    except Exception as e:
        return {"status": "not ready", "database": f"error: {str(e)}"}
```

### Post-Deploy Verification

```bash
# 1. Health checks
curl -f https://app.example.com/health/live
curl -f https://app.example.com/health/ready

# 2. Smoke tests
pytest tests/e2e/test_e2e_ci_smoke.py -v --base-url https://app.example.com

# 3. Performance checks
curl -w "@curl-format.txt" -o /dev/null -s https://app.example.com/api/v1/projects
# Expect: <500ms

# 4. Monitoring dashboards
open https://grafana.example.com  # Check metrics

# 5. Logs
docker-compose -f docker-compose.prod.yml logs -f api | grep ERROR
```

---

## 🔒 Security Hardening

**Status:** ⚠️ **MODERATE SECURITY** (Security Score: 6.5/10)

**Problems:**
- 54 CVE vulnerabilities w dependencies
- Default passwords w docker-compose
- Missing JWT token revocation
- No MFA
- No account lockout

**ACTION REQUIRED (Phase 1 - CRITICAL):** Fix security vulnerabilities

### 1. Remove Default Passwords

**Problem:** docker-compose.yml contains `dev_password_change_in_prod`

**Solution:**
```bash
# Generate strong passwords
export NEO4J_PASSWORD=$(openssl rand -base64 32)
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export SECRET_KEY=$(openssl rand -hex 32)

# Add to .env.production (NOT .env!)
echo "NEO4J_PASSWORD=$NEO4J_PASSWORD" >> .env.production
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" >> .env.production
echo "SECRET_KEY=$SECRET_KEY" >> .env.production

# Validate on startup (app/core/config.py)
class Settings(BaseSettings):
    SECRET_KEY: str

    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        if v in ['change-me', 'dev_password', 'test']:
            raise ValueError("SECRET_KEY must be changed in production!")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters!")
        return v
```

### 2. Upgrade Vulnerable Dependencies

**Problem:** 54 CVEs (9 critical, 23 high, 22 medium/low)

**Critical CVEs:**
- langchain (RCE vulnerabilities)
- aiohttp (request smuggling)
- werkzeug (directory traversal)
- jinja2 (template injection)

**Solution:**
```bash
# Audit dependencies
pip-audit -r requirements.txt --desc

# Upgrade critical packages
pip install --upgrade \
  langchain>=0.1.0 \
  aiohttp>=3.12.14 \
  werkzeug>=3.0.6 \
  jinja2>=3.1.6 \
  cryptography>=44.0.1

# Freeze updated requirements
pip freeze > requirements.txt

# Test after upgrade
pytest tests/ -v
```

### 3. Network Isolation

**Problem:** Databases exposed na host ports (5433, 7687)

**Solution:**
```yaml
# docker-compose.prod.yml
networks:
  internal:  # Database network (NO external access)
    driver: bridge
    internal: true
  external:  # Public-facing services only
    driver: bridge

services:
  postgres:
    networks:
      - internal
    # REMOVE: ports: - "5433:5432"

  neo4j:
    networks:
      - internal
    # REMOVE: ports: - "7687:7687"

  api:
    networks:
      - internal  # Can access databases
      - external  # Can be accessed from frontend
```

### 4. JWT Token Revocation (Phase 2)

**Problem:** Stolen tokens valid 30 min after logout

**Solution:** Redis blacklist
```python
# app/core/security.py
import redis
from datetime import timedelta

redis_client = redis.from_url(settings.REDIS_URL)

async def revoke_token(token: str, expires_in: int):
    """Add token to blacklist"""
    redis_client.setex(f"revoked:{token}", expires_in, "1")

async def is_token_revoked(token: str) -> bool:
    """Check if token is revoked"""
    return redis_client.exists(f"revoked:{token}")

# app/api/auth.py
@router.post("/logout")
async def logout(token: str = Depends(get_current_token)):
    await revoke_token(token, expires_in=1800)  # 30 min
    return {"message": "Logged out successfully"}
```

### 5. Rate Limiting

**Already implemented:** ✅ 5/min login, 3/min register

**Enhance:**
```python
# app/core/security.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# More aggressive limits for sensitive endpoints
@limiter.limit("3/minute")  # Register
@limiter.limit("5/minute")  # Login
@limiter.limit("100/hour")  # General API
```

### 6. Security Headers Middleware

**Already implemented:** ✅ Basic security headers

**Enhance:**
```python
# app/main.py
from stac.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["app.example.com", "*.example.com"]
)

# Custom security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

### Timeline

**Phase 1 (Week 1 - CRITICAL):**
- [ ] Upgrade 54 vulnerable dependencies - 5h
- [ ] Remove default passwords + validation - 2h
- [ ] Network isolation (internal Docker network) - 2h
- [ ] Enhanced security headers - 1h
- [ ] Test security changes - 2h

**Phase 2 (Week 2-3 - HIGH):**
- [ ] Implement JWT token revocation (Redis blacklist) - 6h
- [ ] Add MFA support (TOTP) - 12h
- [ ] Implement account lockout (5 failed attempts) - 6h
- [ ] Security audit + penetration testing - 8h

---

## ⚙️ Resource Management

### Gunicorn Configuration

```python
# app/gunicorn_conf.py
import multiprocessing
import os

# Workers
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000

# Timeouts
timeout = int(os.getenv("TIMEOUT", 120))
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "market-research-api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for better memory sharing
preload_app = True
```

### Database Connection Pooling

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,          # Max connections in pool
    max_overflow=10,       # Extra connections beyond pool_size
    pool_timeout=30,       # Wait 30s for connection
    pool_recycle=3600,     # Recycle connections after 1h
    pool_pre_ping=True,    # Verify connections before use
)
```

### Redis Configuration

```bash
# docker-compose.prod.yml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru --save 60 1000
```

**Maxmemory Policies:**
- `allkeys-lru` - Evict least recently used keys (recommended dla cache)
- `volatile-lru` - Evict LRU keys z TTL
- `noeviction` - Don't evict, return errors (NOT recommended)

### Neo4j Memory Configuration

```yaml
# docker-compose.prod.yml
neo4j:
  environment:
    - NEO4J_server_memory_heap_initial__size=2G
    - NEO4J_server_memory_heap_max__size=4G
    - NEO4J_server_memory_pagecache_size=1G
```

**Recommendations:**
- Heap: 2-4GB depending na dataset size
- Pagecache: 1-2GB dla graph storage
- Total memory: Heap + Pagecache + 1GB overhead

### Docker Resource Limits

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'      # Max 2 CPUs
          memory: 2G       # Max 2GB RAM
        reservations:
          cpus: '1.0'      # Guaranteed 1 CPU
          memory: 1G       # Guaranteed 1GB RAM

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  redis:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G

  neo4j:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

---

## ✅ Production Readiness Checklist

### Phase 1 - MUST DO BEFORE DEPLOY (Week 1)

**Security:**
- [ ] Upgrade all 54 vulnerable dependencies (critical: langchain, aiohttp, werkzeug, jinja2)
- [ ] Remove default passwords (NEO4J_PASSWORD, POSTGRES_PASSWORD, SECRET_KEY)
- [ ] Validate SECRET_KEY in production (not "change-me")
- [ ] Disable DEBUG=false in production
- [ ] Configure ALLOWED_ORIGINS (not *)
- [ ] Network isolation (custom Docker networks, databases internal only)

**Infrastructure:**
- [ ] Automated daily backups enabled (Postgres + Neo4j + Redis)
- [ ] Backup restoration tested (monthly drill)
- [ ] Monitoring deployed (Prometheus + Grafana + Alertmanager)
- [ ] Alerting configured (Slack/PagerDuty on critical events)
- [ ] Health check endpoints (/health/live, /health/ready)
- [ ] Resource limits configured (CPU, memory per service)

**CI/CD:**
- [ ] GitHub Actions workflow configured (.github/workflows/ci.yml)
- [ ] Automated testing in pipeline (unit + integration + E2E smoke)
- [ ] Docker image builds automated (backend + frontend)
- [ ] Vulnerability scanning (Trivy) in pipeline
- [ ] Branch protection rules enabled (require CI pass)

**Testing:**
- [ ] All 380 tests pass
- [ ] Coverage >80% maintained
- [ ] E2E smoke test passes (test_e2e_ci_smoke.py)
- [ ] Performance benchmarks met (persona <60s, focus group <3min)

### Phase 2 - HIGH PRIORITY (Week 2-3)

**Security:**
- [ ] JWT token revocation implemented (Redis blacklist)
- [ ] Account lockout implemented (5 failed attempts)
- [ ] MFA support implemented (TOTP)
- [ ] Security audit completed (OWASP Top 10 compliance)

**Testing:**
- [ ] RAG document ingest tests added (~15 tests)
- [ ] Account lockout tests added (~8 tests)
- [ ] Flaky E2E test fixed (polling loop)

**Infrastructure:**
- [ ] Deployment workflow configured (.github/workflows/deploy.yml)
- [ ] Staging environment setup
- [ ] Log aggregation configured (Loki + Promtail)
- [ ] Advanced dashboards created (LLM Usage, Business Metrics)

### Phase 3 - MEDIUM PRIORITY (Week 3-4)

**Optimization:**
- [ ] AI prompts optimized (700 lines → 250 lines target)
- [ ] Docker images optimized (backend 2.91GB → 450MB, frontend 690MB → 25MB)
- [ ] Redis caching layer implemented (persona profiles, focus group results)
- [ ] Database indexes tuned (slow queries <1s)

**Code Quality:**
- [ ] Long methods refactored (_generate_personas_task: 418 lines → <100 lines)
- [ ] Magic numbers moved to config.py
- [ ] Error handling standardized
- [ ] Persona quality metrics added

---

## 🐛 Troubleshooting

### Docker Issues

#### Problem: "Module not found" po docker-compose up

**Przyczyna:** Konflikt host node_modules vs container

**Rozwiązanie:**
```bash
docker-compose down -v  # Usuń stare volumes
docker-compose up --build -d
```

#### Problem: Frontend robi npm install przy każdym up

**Przyczyna:** Stary docker-compose.yml z `command: npm install`

**Rozwiązanie:**
```bash
# Sprawdź że NIE masz command: npm install w docker-compose.yml
git pull  # Pobierz nowy docker-compose.yml
docker-compose up --build -d
```

#### Problem: Dependencies nie są instalowane

**Przyczyna:** Brak rebuild po zmianie requirements.txt / package.json

**Rozwiązanie:**
```bash
docker-compose up --build -d
```

#### Problem: Cache przestarzały

**Rozwiązanie:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

### CI/CD Issues

#### Problem: Tests fail in CI but pass locally

**Possible causes:**
- Environment variables missing in GitHub Secrets
- Database connection issues (services not healthy)
- Flaky tests (race conditions, timeouts)

**Rozwiązanie:**
```bash
# Run CI tests locally with same conditions
DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5432/test_db \
pytest tests/ -v --run-slow --run-external
```

#### Problem: Docker build fails in CI (out of disk space)

**Rozwiązanie:**
```yaml
# .github/workflows/ci.yml
- name: Clean up Docker
  run: docker system prune -af --volumes
```

### Monitoring Issues

#### Problem: Prometheus not scraping metrics

**Rozwiązanie:**
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Check if /metrics endpoint works
curl http://localhost:8000/metrics

# Check Prometheus logs
docker-compose -f docker-compose.monitoring.yml logs prometheus
```

#### Problem: Grafana dashboards not showing data

**Rozwiązanie:**
```bash
# Check datasource configuration
# Grafana → Configuration → Data Sources → Prometheus
# URL should be: http://prometheus:9090

# Test query in Grafana Explore
rate(http_requests_total[5m])
```

### Backup Issues

#### Problem: Backup script fails (pg_dump error)

**Rozwiązanie:**
```bash
# Check if Postgres is running
docker-compose ps postgres

# Check Postgres logs
docker-compose logs postgres

# Test pg_dump manually
docker-compose exec postgres pg_dump -U market_research market_research_db > test_backup.sql
```

#### Problem: S3 upload fails (permission denied)

**Rozwiązanie:**
```bash
# Check AWS credentials
aws s3 ls s3://my-backups-bucket/

# Check IAM permissions (needs s3:PutObject, s3:GetObject, s3:DeleteObject)
aws iam get-user-policy --user-name backup-user --policy-name BackupPolicy
```

---

## 📚 Best Practices

1. **Layer caching** - kopiuj dependencies files PRZED kodem
2. **Multi-stage** - oddziel build dependencies od runtime
3. **.dockerignore** - wyklucz niepotrzebne pliki (szybsze buildy)
4. **Named volumes** - zapobiega konfliktom host vs container
5. **Non-root user** - security best practice
6. **Healthchecks** - zapewnij że services są ready przed startem
7. **Resource limits** - zapobiega resource exhaustion w production
8. **Monitoring** - Prometheus + Grafana od day 1
9. **Backups** - Automated daily z 30-day retention + monthly DR drill
10. **CI/CD** - Automated testing + deployment, branch protection

---

## 📞 Kontakt

**Problemy z DevOps?**
1. Sprawdź [Troubleshooting](#troubleshooting)
2. Sprawdź logi: `docker-compose logs`
3. Sprawdź monitoring dashboards (Grafana)
4. Otwórz issue na GitHubie

---

**Ostatnia aktualizacja:** 2025-10-15 (Major update: DevOps documentation)
**Wersja:** 1.0 (Created based on audit results)
**DevOps Maturity:** Level 2 (Defined) → Target: Level 3 (Managed)
