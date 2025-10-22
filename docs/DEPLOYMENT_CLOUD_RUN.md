# Deployment na Google Cloud Run

**Ostatnia aktualizacja:** 2025-10-22
**Status:** Production-ready

---

## Przegląd

Ten dokument opisuje deployment aplikacji **Sight** (Market Research SaaS) na Google Cloud Run.

**Architektura:**
- **Kontener:** FastAPI + Gunicorn (multi-stage Dockerfile)
- **Baza danych:** Cloud SQL (PostgreSQL)
- **Cache:** Memorystore (Redis)
- **Graf:** Neo4j AuraDB (managed service)
- **Sekrety:** Secret Manager
- **Build:** Cloud Build (CI/CD)

---

## Wymagania

### 1. GCP Services

Aktywuj następujące API:
```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  artifactregistry.googleapis.com
```

### 2. Artifact Registry

Stwórz Docker repository:
```bash
gcloud artifacts repositories create sight-repo \
  --repository-format=docker \
  --location=europe-central2 \
  --description="Sight Market Research SaaS images"
```

---

## Konfiguracja Secrets

### Secret Manager

Dodaj sekretne zmienne:
```bash
# Google Gemini API Key
echo -n "your-gemini-api-key" | gcloud secrets create GOOGLE_API_KEY \
  --data-file=- \
  --replication-policy=automatic

# FastAPI Secret Key (generuj silny)
echo -n "$(openssl rand -hex 32)" | gcloud secrets create SECRET_KEY \
  --data-file=- \
  --replication-policy=automatic

# Database URL (Cloud SQL connector używa IAM)
echo -n "postgresql+asyncpg://sight:PASSWORD@/sight_db?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME" | \
  gcloud secrets create DATABASE_URL \
  --data-file=- \
  --replication-policy=automatic

# Neo4j credentials
echo -n "neo4j+s://YOUR_AURA_URI" | gcloud secrets create NEO4J_URI --data-file=-
echo -n "neo4j" | gcloud secrets create NEO4J_USER --data-file=-
echo -n "YOUR_PASSWORD" | gcloud secrets create NEO4J_PASSWORD --data-file=-

# Redis (Memorystore)
echo -n "redis://10.x.x.x:6379/0" | gcloud secrets create REDIS_URL --data-file=-
```

---

## Build & Deploy

### 1. Build Docker Image

**Cloud Build (automated):**
```bash
gcloud builds submit \
  --tag europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:latest
```

**Local build + push:**
```bash
# Build
docker build -t europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:latest .

# Auth
gcloud auth configure-docker europe-central2-docker.pkg.dev

# Push
docker push europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:latest
```

### 2. Cloud SQL Setup

```bash
# Stwórz instancję
gcloud sql instances create sight-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-central2

# Stwórz użytkownika
gcloud sql users create sight --instance=sight-db --password=STRONG_PASSWORD

# Stwórz bazę
gcloud sql databases create sight_db --instance=sight-db
```

### 3. Memorystore Redis

```bash
gcloud redis instances create sight-cache \
  --size=1 \
  --region=europe-central2 \
  --redis-version=redis_7_0
```

### 4. Deploy Cloud Run

```bash
gcloud run deploy sight \
  --image europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:latest \
  --platform managed \
  --region europe-central2 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 120 \
  --max-instances 10 \
  --min-instances 1 \
  --concurrency 16 \
  --set-env-vars "ENVIRONMENT=production,DEBUG=false" \
  --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest,NEO4J_URI=NEO4J_URI:latest,NEO4J_USER=NEO4J_USER:latest,NEO4J_PASSWORD=NEO4J_PASSWORD:latest,REDIS_URL=REDIS_URL:latest" \
  --add-cloudsql-instances PROJECT_ID:europe-central2:sight-db \
  --vpc-connector projects/PROJECT_ID/locations/europe-central2/connectors/sight-connector
```

**Parametry:**
- `--memory 4Gi` - RAG + sentence-transformers + Neo4j operations wymagają ~2-3 Gi
- `--cpu 2` - Rekomendowane dla LLM operations
- `--concurrency 16` - Ile requestów na instancję (adjust based on load)
- `--min-instances 1` - Warm instance (unikaj cold start)

---

## Database Migrations

### Strategia

**NIE uruchamiaj migracji w entrypoint produkcji** (race conditions).

**Opcja 1: Cloud Build Step (recommended)**

Dodaj step do `cloudbuild.yaml`:
```yaml
steps:
  # Build image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'image-url', '.']

  # Run migrations
  - name: 'image-url'
    entrypoint: 'alembic'
    args: ['upgrade', 'head']
    env:
      - 'DATABASE_URL=$$DATABASE_URL'
    secretEnv: ['DATABASE_URL']

  # Push image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'image-url']

availableSecrets:
  secretManager:
    - versionName: projects/PROJECT_ID/secrets/DATABASE_URL/versions/latest
      env: 'DATABASE_URL'
```

**Opcja 2: Cloud Run Job**

Stwórz osobny Cloud Run Job dla migracji:
```bash
gcloud run jobs create sight-migrations \
  --image europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:latest \
  --region europe-central2 \
  --command alembic,upgrade,head \
  --set-secrets DATABASE_URL=DATABASE_URL:latest \
  --add-cloudsql-instances PROJECT_ID:europe-central2:sight-db
```

Uruchom przed deploy:
```bash
gcloud run jobs execute sight-migrations --region europe-central2 --wait
```

---

## Monitoring & Logging

### Health Checks

Cloud Run używa `/health` endpoint:
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Logs

```bash
# Streaming logs
gcloud run services logs tail sight --region europe-central2

# Filter errors
gcloud logging read 'resource.type=cloud_run_revision AND severity>=ERROR' \
  --limit 50 --format json

# Filter LLM errors
gcloud logging read 'textPayload=~"LLMGraphTransformer" OR textPayload=~"RAG"' \
  --limit 20
```

### Metrics

Dashboard w Cloud Console → Cloud Run → sight → Metrics:
- Request count & latency
- Instance count (autoscaling)
- Memory & CPU usage
- Error rate

---

## Troubleshooting

### 503 Service Unavailable

**Przyczyny:**
1. Container OOM (out of memory) → zwiększ `--memory`
2. Timeout (request >120s) → zwiększ `--timeout` lub async optimization
3. Cold start z dużym obrazem → użyj `--min-instances 1`

**Debug:**
```bash
# Check revision logs
gcloud run revisions list --service sight --region europe-central2
gcloud run revisions describe REVISION_NAME --region europe-central2
```

### Database Connection Issues

**Cloud SQL Connector:**
- Sprawdź czy instancja działa: `gcloud sql instances describe sight-db`
- Sprawdź czy connector jest w `--add-cloudsql-instances`
- Sprawdź format DATABASE_URL: `postgresql+asyncpg://user:pass@/db?host=/cloudsql/PROJECT:REGION:INSTANCE`

### Neo4j Timeouts

**AuraDB:**
- Sprawdź firewall rules (AuraDB używa publicznego IP)
- Użyj `neo4j+s://` (secure connection)
- Connection pooling: `max_connection_pool_size=50` w config

---

## Cost Optimization

### Tips

1. **Auto-scaling:** `--min-instances 0` dla dev, `1` dla prod (trade-off: cold start vs cost)
2. **CPU allocation:** `--cpu-throttling` (default) - CPU tylko podczas requestów
3. **Memory:** Start z 2Gi, zwiększ tylko jeśli OOM
4. **Cloud SQL:** `db-f1-micro` dla dev, `db-custom-2-7680` dla prod
5. **Memorystore:** 1GB wystarczy dla cache (Redis TTL 1h)

### Estimated Costs (monthly)

- Cloud Run: ~$20-50 (zależy od traffic)
- Cloud SQL: ~$10-30 (f1-micro)
- Memorystore: ~$30 (1GB)
- Neo4j AuraDB: ~$65 (Free tier dostępny)
- **Total:** ~$125-175/month (low-medium traffic)

---

## CI/CD Pipeline

### GitHub Actions (przykład)

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Auth GCP
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build & Push
        run: |
          gcloud builds submit --tag IMAGE_URL

      - name: Run Migrations
        run: |
          gcloud run jobs execute sight-migrations --wait

      - name: Deploy
        run: |
          gcloud run deploy sight --image IMAGE_URL --region europe-central2
```

---

## Kolejne Kroki

1. **Setup monitoring:** Cloud Monitoring dashboards + alerting
2. **CDN:** Cloud CDN dla static files (avatary użytkowników)
3. **Load testing:** `locust` lub `k6` dla performance baseline
4. **Backups:** Automated Cloud SQL backups (enabled by default)
5. **Disaster recovery:** Multi-region deployment (advanced)

**Pytania?** Zobacz: https://cloud.google.com/run/docs
