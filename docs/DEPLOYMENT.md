# Deployment - GCP Cloud Run

Kompletny przewodnik deployment aplikacji Sight na Google Cloud Platform (Cloud Run).

**Ostatnia aktualizacja:** 2025-10-21

## Przegląd Architektury Production

### Single Service Architecture
- **Backend + Frontend** w jednym kontenerze Docker
- FastAPI serwuje React SPA jako static files
- Automatyczny deployment przez GitHub Actions + Cloud Build

### Infrastruktura

```
┌─────────────────────────────────────────────────────────┐
│                    Cloud Run Service                    │
│                        (sight)                          │
│  ┌────────────┐              ┌──────────────┐          │
│  │  Frontend  │              │   Backend    │          │
│  │  (React)   │◄────────────►│  (FastAPI)   │          │
│  │  /static/  │              │  /api/v1/*   │          │
│  └────────────┘              └──────┬───────┘          │
│                                     │                   │
└─────────────────────────────────────┼───────────────────┘
                                      │
                    ┌─────────────────┼──────────────────┐
                    │                 │                  │
                    ▼                 ▼                  ▼
            ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
            │  Cloud SQL   │  │  Neo4j Aura  │  │Upstash Redis │
            │ (PostgreSQL) │  │ (Graph DB)   │  │   (Cache)    │
            └──────────────┘  └──────────────┘  └──────────────┘
```

**Komponenty:**
- **Cloud Run**: Managed containerized app (auto-scaling 0-5 instances)
- **Cloud SQL**: PostgreSQL 15 (db-f1-micro, 10GB SSD)
- **Neo4j AuraDB**: Graph database dla RAG (Free tier, 50k nodes)
- **Upstash Redis**: Serverless cache (Free tier, 10k requests/day)
- **Artifact Registry**: Docker images storage
- **Secret Manager**: Bezpieczne przechowywanie credentials

---

## Wymagania Wstępne

### 1. Google Cloud Platform

**Setup projektu:**
```bash
# Zaloguj się do GCP
gcloud auth login

# Ustaw projekt
gcloud config set project gen-lang-client-0508446677

# Włącz wymagane API
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com
```

### 2. Zewnętrzne Serwisy

**Neo4j AuraDB (Graph Database):**
1. Utwórz konto: https://neo4j.com/cloud/aura/
2. Utwórz instancję: **AuraDB Free** (50k nodes, $0/mies)
3. Region: **europe-west1** (najbliżej europe-central2)
4. Zapisz credentials:
   - `NEO4J_URI`: `neo4j+s://xxxxx.databases.neo4j.io`
   - `NEO4J_USER`: `neo4j` (default)
   - `NEO4J_PASSWORD`: [twoje hasło]

**Upstash Redis (Cache):**
1. Utwórz konto: https://upstash.com/
2. Utwórz Redis database: **Free tier** (10k requests/day)
3. Region: **europe-west1**
4. Zapisz connection string:
   - Format: `redis://default:PASSWORD@region.upstash.io:PORT`
   - Znajdź w: **Details → Redis Connect → Node.js**

**Google Gemini API:**
1. Utwórz API key: https://aistudio.google.com/app/apikey
2. Zapisz `GOOGLE_API_KEY`

### 3. Cloud SQL (PostgreSQL)

**Utwórz instancję Cloud SQL:**
```bash
# Sprawdź czy instancja już istnieje
gcloud sql instances describe sight --region=europe-central2

# Jeśli nie istnieje, utwórz:
gcloud sql instances create sight \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=europe-central2 \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=04

# Utwórz bazę danych
gcloud sql databases create sight_db --instance=sight

# Ustaw hasło dla użytkownika postgres
gcloud sql users set-password postgres \
  --instance=sight \
  --password=[SECURE_PASSWORD]

# Zapisz hasło! Będzie użyte w sekretach.
```

**Connection string format:**
```
postgresql+asyncpg://postgres:PASSWORD@/sight_db?host=/cloudsql/gen-lang-client-0508446677:europe-central2:sight
```

---

## Konfiguracja Secrets

### Automatyczna Konfiguracja (Zalecane)

**Użyj skryptu `setup-gcp-secrets.sh`:**
```bash
chmod +x scripts/setup-gcp-secrets.sh
./scripts/setup-gcp-secrets.sh
```

Skrypt automatycznie:
- Tworzy/aktualizuje wszystkie wymagane secrets
- Generuje `SECRET_KEY` (FastAPI session key)
- Buduje `DATABASE_URL_CLOUD` z `POSTGRES_PASSWORD`
- Nadaje uprawnienia Cloud Run service account

### Manualna Konfiguracja

**Wymagane secrets:**
```bash
# 1. Google Gemini API Key
echo -n "your_gemini_api_key" | gcloud secrets create GOOGLE_API_KEY --data-file=-

# 2. Neo4j AuraDB
echo -n "neo4j+s://xxxxx.databases.neo4j.io" | gcloud secrets create NEO4J_URI --data-file=-
echo -n "your_neo4j_password" | gcloud secrets create NEO4J_PASSWORD --data-file=-

# 3. Upstash Redis
echo -n "redis://default:password@region.upstash.io:port" | gcloud secrets create REDIS_URL --data-file=-

# 4. Cloud SQL
POSTGRES_PASSWORD="your_secure_password"
echo -n "$POSTGRES_PASSWORD" | gcloud secrets create POSTGRES_PASSWORD --data-file=-
echo -n "postgresql+asyncpg://postgres:${POSTGRES_PASSWORD}@/sight_db?host=/cloudsql/gen-lang-client-0508446677:europe-central2:sight" | gcloud secrets create DATABASE_URL_CLOUD --data-file=-

# 5. FastAPI Secret Key
openssl rand -hex 32 | gcloud secrets create SECRET_KEY --data-file=-
```

**Grant access to Cloud Run:**
```bash
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

for SECRET in GOOGLE_API_KEY NEO4J_URI NEO4J_PASSWORD REDIS_URL DATABASE_URL_CLOUD POSTGRES_PASSWORD SECRET_KEY; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
done
```

**Weryfikacja:**
```bash
# Lista wszystkich secrets
gcloud secrets list --filter="labels.app=sight"

# Sprawdź wartość (dla debugowania)
gcloud secrets versions access latest --secret="NEO4J_URI"
```

---

## Deployment

### GitHub CI/CD (Automatyczny) - ZALECANE

**Setup (już skonfigurowane):**
- Cloud Build trigger podpięty do repo: `JakWdo/Symulacja`
- Branch: `cleanup/dead-code-removal`
- Config: `cloudbuild.yaml`

**Workflow:**
```bash
# 1. Commit zmiany
git add .
git commit -m "feat: Your feature description"

# 2. Push do GitHub
git push origin cleanup/dead-code-removal

# 3. Cloud Build automatycznie wystartuje:
#    - Build Docker image (Dockerfile.cloudrun)
#    - Push do Artifact Registry
#    - Deploy na Cloud Run service: sight

# 4. Monitoruj build
gcloud builds list --limit=1 --format="table(id,status,createTime)"

# 5. Stream logs
BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)")
gcloud builds log $BUILD_ID --stream
```

**Sprawdź status deployment:**
```bash
# Service details
gcloud run services describe sight --region=europe-central2

# Get URL
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")
echo "Deployed to: $SERVICE_URL"

# Health check
curl $SERVICE_URL/health
```

### Manual Deployment

**Dla testów lub one-off deployments:**
```bash
# Submit build manually
gcloud builds submit --config cloudbuild.yaml

# Lub build lokalnie i deploy
docker build -f Dockerfile.cloudrun -t sight:latest .
docker tag sight:latest europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest
docker push europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest

gcloud run deploy sight \
  --image=europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  --region=europe-central2 \
  --platform=managed \
  --allow-unauthenticated
```

---

## Post-Deployment Setup

### 1. Migracje Bazy Danych

**OPCJA A: Cloud Run Job (zalecane):**
```bash
# Utwórz job dla migracji
gcloud run jobs create db-migrate \
  --image=europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  --region=europe-central2 \
  --add-cloudsql-instances=gen-lang-client-0508446677:europe-central2:sight \
  --set-secrets=DATABASE_URL=DATABASE_URL_CLOUD:latest \
  --command="alembic,upgrade,head"

# Uruchom migracje
gcloud run jobs execute db-migrate --region=europe-central2 --wait

# Sprawdź logi
gcloud run jobs executions logs <EXECUTION_ID>
```

**OPCJA B: Cloud SQL Proxy (lokalnie):**
```bash
# Pobierz Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Uruchom proxy
./cloud_sql_proxy -instances=gen-lang-client-0508446677:europe-central2:sight=tcp:5432 &

# Ustaw DATABASE_URL (lokalnie)
export DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@localhost:5432/sight_db"

# Uruchom migracje
alembic upgrade head
```

### 2. Inicjalizacja Neo4j Indexes

**WAŻNE: Wymagane dla RAG system!**

**OPCJA A: Przez API endpoint:**
```bash
# Pobierz URL serwisu
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")

# Wywołaj endpoint inicjalizacji (wymaga auth token)
# TODO: Endpoint /api/v1/rag/init-indexes wymaga implementacji
curl -X POST "$SERVICE_URL/api/v1/rag/init-indexes"
```

**OPCJA B: Lokalnie przez port-forward:**
```bash
# Port-forward Cloud Run service
gcloud run services proxy sight --region=europe-central2 --port=8080 &

# Wywołaj endpoint
curl -X POST http://localhost:8080/api/v1/rag/init-indexes
```

**OPCJA C: Bezpośrednio w Neo4j AuraDB:**
```cypher
// Login do Neo4j Browser: https://console.neo4j.io/
// Wybierz swoją instancję → Open with Neo4j Browser

// Create indexes
CREATE INDEX document_id_idx IF NOT EXISTS FOR (d:Document) ON (d.id);
CREATE INDEX chunk_embedding_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding);
CREATE VECTOR INDEX chunk_vector_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding)
  OPTIONS {indexConfig: {`vector.dimensions`: 3072, `vector.similarity_function`: 'cosine'}};
```

### 3. Weryfikacja Deployment

**Health checks:**
```bash
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")

# Backend health
curl $SERVICE_URL/health

# API docs
open "$SERVICE_URL/docs"

# Frontend
open $SERVICE_URL

# Test API endpoint
curl $SERVICE_URL/api/v1/projects
```

**Sprawdź logi:**
```bash
# Real-time logs
gcloud run services logs read sight --region=europe-central2 --limit=50 --follow

# Errors only
gcloud run services logs read sight --region=europe-central2 --limit=50 --log-filter="severity>=ERROR"

# Specific timestamp
gcloud run services logs read sight --region=europe-central2 --after="2025-10-21T10:00:00Z"
```

**Metrics:**
```bash
# Cloud Console → Cloud Run → sight → Metrics
# Lub CLI:
gcloud monitoring timeseries list \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="sight"' \
  --format="table(metric.type,points[0].value)"
```

---

## Monitoring & Debugging

### Logs

**Cloud Logging queries:**
```bash
# All logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight" --limit=100

# Errors only
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight AND severity>=ERROR" --limit=50

# Search for keyword
gcloud logging read "resource.type=cloud_run_revision AND textPayload=~\"RAG\"" --limit=20
```

### Common Issues

**1. Service nie startuje (timeout):**
```bash
# Sprawdź startup logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight" --limit=100 --format="value(textPayload)"

# Możliwe przyczyny:
# - RAG eager initialization (FIXED: commit 11a002b)
# - Brak dostępu do secrets
# - Cloud SQL connection timeout
```

**2. Frontend 404:**
```bash
# Sprawdź czy static files są w image:
# (wymagany exec do running container - nie możliwe w Cloud Run)
# Alternatywa: rebuild lokalnie i sprawdź
docker build -f Dockerfile.cloudrun -t test:latest .
docker run -it --entrypoint /bin/bash test:latest
ls -la /app/static/
```

**3. Database connection errors:**
```bash
# Sprawdź Cloud SQL status
gcloud sql instances describe sight --region=europe-central2

# Sprawdź secret DATABASE_URL_CLOUD
gcloud secrets versions access latest --secret="DATABASE_URL_CLOUD"

# Zweryfikuj connection string format:
# postgresql+asyncpg://postgres:PASSWORD@/sight_db?host=/cloudsql/PROJECT:REGION:INSTANCE
```

**4. Neo4j timeout:**
```bash
# Sprawdź Neo4j AuraDB status (console.neo4j.io)
# Sprawdź firewall: dodaj 0.0.0.0/0 dla Cloud Run (dynamiczne IP)
# Sprawdź secret NEO4J_URI
gcloud secrets versions access latest --secret="NEO4J_URI"
```

---

## Rollback & Updates

### Rollback do poprzedniej wersji

```bash
# Lista rewizji
gcloud run revisions list --service=sight --region=europe-central2

# Rollback do poprzedniej rewizji
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=sight-00042-xyz=100

# Canary deployment (50% traffic split)
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=sight-00043-new=50,sight-00042-old=50
```

### Update env vars lub secrets

```bash
# Dodaj nową env var
gcloud run services update sight \
  --region=europe-central2 \
  --set-env-vars="NEW_VAR=value"

# Zaktualizuj secret
echo -n "new_value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Cloud Run automatycznie użyje latest version secrets
```

---

## Koszty (Szacunkowe)

**Miesięczne koszty dla małego projektu (~100 users, 1000 requests/day):**

| Serwis | Tier | Koszt/mies |
|--------|------|------------|
| Cloud Run (sight) | 2Gi RAM, 1 vCPU | $5-10 |
| Cloud SQL (db-f1-micro) | 10GB SSD | $10-15 |
| Neo4j AuraDB Free | 50k nodes | $0 |
| Upstash Redis Free | 10k req/day | $0 |
| Cloud Build | <120 min/day | $0-2 |
| Artifact Registry | Storage + egress | $1-3 |
| Secret Manager | 7 secrets | $0 (included) |
| **TOTAL** | | **~$16-30/mies** |

**Optymalizacje kosztów:**
- Cloud Run auto-scales to 0 (pay only when running)
- Cloud SQL: backup retention = 7 days (default)
- Używaj Cloud Build cache dla szybszych buildów

---

## Security Checklist

- [x] Secrets w Secret Manager (nie w env vars/repo)
- [x] Cloud SQL private IP (przez Unix socket `/cloudsql/`)
- [x] Non-root user w Docker (UID 1000)
- [x] SECRET_KEY minimum 32 chars (random hex)
- [x] CORS restricted (tylko production domain)
- [x] HTTPS only (Cloud Run default)
- [x] Security headers middleware (CSP, X-Frame-Options, etc.)
- [x] Rate limiting (slowapi)
- [ ] VPC connector dla private Neo4j/Redis (opcjonalnie)
- [ ] Cloud Armor (WAF) - dla większych projektów

---

## Useful Commands Reference

```bash
# Deployment
gcloud builds submit --config cloudbuild.yaml
gcloud run deploy sight --image=IMAGE_URL --region=europe-central2

# Monitoring
gcloud run services logs read sight --region=europe-central2 --limit=50 --follow
gcloud run services describe sight --region=europe-central2

# Secrets
gcloud secrets list
gcloud secrets versions access latest --secret="SECRET_NAME"

# Cloud SQL
gcloud sql instances describe sight --region=europe-central2
gcloud sql databases list --instance=sight

# Debugging
gcloud run revisions list --service=sight --region=europe-central2
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50
```

---

## Next Steps

1. ✅ Konfiguracja secrets (`./scripts/setup-gcp-secrets.sh`)
2. ✅ Weryfikacja Cloud SQL (`gcloud sql instances describe sight`)
3. ✅ Deploy aplikacji (`git push origin cleanup/dead-code-removal`)
4. ⏳ Migracje bazy (Cloud Run Job)
5. ⏳ Inicjalizacja Neo4j indexes
6. ⏳ Weryfikacja health checks
7. ⏳ Setup custom domain (opcjonalnie)
8. ⏳ Configure monitoring alerts (opcjonalnie)

**Dodatkowa dokumentacja:**
- [Cloud Run docs](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Dockerfile best practices](https://docs.docker.com/develop/dev-best-practices/)
