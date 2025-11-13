# 🚀 DEPLOY.md - Sight Platform Deployment Guide

Kompletny przewodnik po procesie wdrożeniowym platformy Sight na Google Cloud Run.

## 📑 Spis treści

1. [Przegląd Architektury](#przegląd-architektury)
2. [Wymagania Wstępne](#wymagania-wstępne)
3. [Środowiska](#środowiska)
4. [Proces Deployment](#proces-deployment)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring i Debugging](#monitoring-i-debugging)
7. [Troubleshooting](#troubleshooting)

---

## Przegląd Architektury

### Pipeline Deployment (cloudbuild.yaml)

```
┌─────────────────────────────────────────────────────────────────┐
│  STAGING FIRST → PRODUCTION AFTER                               │
└─────────────────────────────────────────────────────────────────┘

1. BUILD                  Docker image (frontend + backend)
   ↓
2. PUSH                   Artifact Registry
   ↓
3. MIGRATE               Database migrations (production DB)
   ↓
4. DEPLOY STAGING        sight-staging service (separate DB)
   ↓
5. SMOKE TESTS STAGING   Health + Frontend checks
   │                     ❌ FAIL → ABORT (no production deploy)
   ↓ ✅ PASS
6. DEPLOY PRODUCTION     New revision with --no-traffic (0%)
   ↓
7. NEO4J INIT           Initialize vector indexes
   ↓
8. SMOKE TESTS PROD     Test new revision (tag URL)
   │                    ❌ FAIL → AUTO-ROLLBACK
   ↓ ✅ PASS
9. TRAFFIC PROMOTION    Gradual rollout:
   │                    10% (canary) → 50% → 100%
   │                    ❌ CANARY FAIL → AUTO-ROLLBACK
   ↓ ✅ SUCCESS
10. DEPLOYMENT COMPLETE  100% traffic on new revision
```

### Środowiska

| Environment | Service Name     | Database            | URL                                                      |
|-------------|------------------|---------------------|----------------------------------------------------------|
| **Staging** | `sight-staging`  | `sight-staging` DB  | https://sight-staging-193742683473.europe-central2.run.app |
| **Production** | `sight`        | `sight` DB          | https://sight-193742683473.europe-central2.run.app       |

---

## Wymagania Wstępne

### 1. GCP Setup

```bash
# Zaloguj się do GCP
gcloud auth login
gcloud config set project gen-lang-client-0508446677

# Sprawdź obecne środowisko
gcloud config list
```

### 2. Sekrety GCP Secret Manager

#### Production Secrets
Użyj skryptu `scripts/setup-gcp-secrets.sh` do utworzenia sekretów produkcyjnych:

```bash
./scripts/setup-gcp-secrets.sh
```

Wymagane sekrety (production):
- `GOOGLE_API_KEY` - Gemini API key
- `DATABASE_URL_CLOUD` - PostgreSQL connection string
- `POSTGRES_PASSWORD` - PostgreSQL password
- `SECRET_KEY` - FastAPI JWT signing key
- `NEO4J_URI` - Neo4j AuraDB URI
- `NEO4J_PASSWORD` - Neo4j password
- `REDIS_URL` - Redis connection string

#### Staging Secrets
Użyj skryptu `scripts/setup-gcp-secrets-staging.sh` do utworzenia sekretów staging:

```bash
./scripts/setup-gcp-secrets-staging.sh
```

Wymagane sekrety (staging) - z sufiksem `_STAGING`:
- `GOOGLE_API_KEY_STAGING`
- `DATABASE_URL_STAGING`
- `POSTGRES_PASSWORD_STAGING`
- `SECRET_KEY_STAGING`
- `NEO4J_URI_STAGING`
- `NEO4J_PASSWORD_STAGING`
- `REDIS_URL_STAGING`

⚠️ **WAŻNE:**
- `POSTGRES_PASSWORD_STAGING` i `SECRET_KEY_STAGING` **MUSZĄ** być inne niż production
- `GOOGLE_API_KEY` może być ten sam (opcjonalnie osobny staging API key)
- Neo4j i Redis mogą używać tych samych instancji (ale zalecamy osobne dla staging)

### 3. Cloud SQL Instances

#### Production Database
```bash
# Sprawdź czy istnieje
gcloud sql instances describe sight --region=europe-central2

# Jeśli nie istnieje, utwórz
gcloud sql instances create sight \
  --database-version=POSTGRES_15 \
  --tier=db-custom-2-7680 \
  --region=europe-central2 \
  --backup-start-time=02:00
```

#### Staging Database
```bash
# Utwórz osobną instancję dla staging
gcloud sql instances create sight-staging \
  --database-version=POSTGRES_15 \
  --tier=db-custom-1-3840 \
  --region=europe-central2 \
  --backup-start-time=03:00

# Utwórz bazę danych
gcloud sql databases create sight_db_staging \
  --instance=sight-staging
```

### 4. Cloud Run Services

Services są tworzone automatycznie podczas pierwszego deployment przez Cloud Build.

Możesz stworzyć je manualnie (opcjonalne):

```bash
# Staging service (opcjonalne - Cloud Build utworzy automatycznie)
gcloud run services create sight-staging \
  --region=europe-central2 \
  --platform=managed

# Production service (opcjonalne - Cloud Build utworzy automatycznie)
gcloud run services create sight \
  --region=europe-central2 \
  --platform=managed
```

---

## Proces Deployment

### Automatyczny Deployment (Recommended)

**Każdy push do branch `main` automatycznie triggeruje Cloud Build:**

```bash
# 1. Commit changes
git add .
git commit -m "feat: nowa funkcjonalność"

# 2. Push do main
git push origin main

# 3. Monitoruj build
gcloud builds list --limit=1 --ongoing
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

### Ręczny Deployment

Jeśli chcesz zdeployować lokalnie (bez push do GitHub):

```bash
# Submit build ręcznie
gcloud builds submit \
  --config=cloudbuild.yaml \
  --region=europe-central2

# Lub z konkretnym tagiem
gcloud builds submit \
  --config=cloudbuild.yaml \
  --region=europe-central2 \
  --substitutions=TAG_NAME=v1.2.3
```

### Pipeline Stages

#### Stage 1-3: Build, Push, Migrate
```
✅ BUILD    → Docker image (8-12 min with cache)
✅ PUSH     → europe-central2-docker.pkg.dev
✅ MIGRATE  → Database migrations via Cloud Run Jobs
```

#### Stage 4-5: Staging Deployment
```
✅ DEPLOY STAGING     → sight-staging service
✅ SMOKE TESTS STAGING → /health + frontend checks (3 retries)
   ❌ FAIL → ABORT entire pipeline (no production deploy)
```

**Staging jako Gate:** Jeśli staging failuje, production deployment NIE zostanie uruchomiony.

#### Stage 6-7: Production Deployment (No Traffic)
```
✅ DEPLOY PRODUCTION → New revision with --no-traffic (0%)
✅ NEO4J INIT       → Vector indexes initialization
```

Nowa rewizja jest deployed, ale **NIE otrzymuje traffic**. Users nadal widzą poprzednią rewizję.

#### Stage 8: Production Smoke Tests
```
✅ SMOKE TESTS PROD → Test new revision via tag URL
   https://REVISION---sight-193742683473.europe-central2.run.app

   Tests:
   - /health endpoint (3 retries, 10s intervals)
   - Frontend / (3 retries, 10s intervals)

   ❌ FAIL → AUTO-ROLLBACK (traffic stays on old revision)
```

#### Stage 9: Traffic Promotion (Canary Deployment)
```
🚦 TRAFFIC PROMOTION

Phase 1: 10% canary
  ↓ NEW=10%, OLD=90%
  ↓ Monitor 30s
  ↓ Health check
  ❌ FAIL → ROLLBACK to 100% OLD

Phase 2: 50% split
  ↓ NEW=50%, OLD=50%
  ↓ Monitor 20s

Phase 3: 100% new
  ✅ NEW=100%
  ✅ DEPLOYMENT COMPLETE
```

**Canary failure triggers automatic rollback** - traffic wraca do 100% na starą rewizję.

---

## Rollback Procedures

### Automatyczny Rollback

Pipeline automatycznie rollbackuje w przypadkach:

1. **Staging smoke tests fail** → Abort, no production deploy
2. **Production smoke tests fail** → Rollback to previous revision
3. **Canary health check fail** → Rollback to previous revision

```bash
# Automatyczny rollback jest wykonywany przez step 'auto-rollback'
# Nie wymaga interwencji manualnej
```

### Ręczny Rollback (Emergency)

Jeśli zauważysz problemy po deployment:

#### Metoda 1: Rollback do poprzedniej rewizji (FASTEST)

```bash
# 1. Lista rewizji
gcloud run revisions list \
  --service=sight \
  --region=europe-central2 \
  --limit=5

# Output:
# REVISION                      ACTIVE  SERVICE  DEPLOYED
# sight-00042-abc              ✔       sight    2025-11-13 14:30:00
# sight-00041-xyz                      sight    2025-11-13 12:00:00  ← PREVIOUS (rollback target)

# 2. Natychmiastowy rollback (100% traffic na previous)
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=sight-00041-xyz=100

# Czas wykonania: ~5-10 sekund
# Users natychmiast widzą poprzednią wersję
```

#### Metoda 2: Gradual rollback (SAFER)

```bash
# Jeśli chcesz stopniowo wrócić (canary rollback)

# Step 1: 50% rollback
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=sight-00041-xyz=50,sight-00042-abc=50

# Step 2: Monitor errors for 5-10 minutes
# Check logs, error rates, user reports

# Step 3: Complete rollback (if issues persist)
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=sight-00041-xyz=100
```

#### Metoda 3: Rollback do konkretnej wersji (TARGETED)

```bash
# Jeśli potrzebujesz wrócić do konkretnej wersji (np. sprzed 3 dni)

# 1. Znajdź rewizję
gcloud run revisions list \
  --service=sight \
  --region=europe-central2 \
  --filter="metadata.creationTimestamp>'2025-11-10'" \
  --format="table(metadata.name,status.conditions[0].lastTransitionTime)"

# 2. Rollback do wybranej rewizji
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=sight-00035-def=100
```

### Rollback Checklist

Po wykonaniu rollback:

- [ ] Sprawdź traffic distribution: `gcloud run services describe sight --region=europe-central2`
- [ ] Weryfikuj /health endpoint: `curl https://sight-193742683473.europe-central2.run.app/health`
- [ ] Sprawdź logi błędów: `gcloud logging read 'resource.type=cloud_run_revision AND severity>=ERROR' --limit=50`
- [ ] Zidentyfikuj przyczynę problemu (przed następnym deployment)
- [ ] Usuń failed revision (opcjonalnie): `gcloud run revisions delete sight-00042-abc --region=europe-central2`

---

## Monitoring i Debugging

### Sprawdzanie Statusu Deployment

```bash
# Status Cloud Build
gcloud builds list --limit=5

# Status konkretnego build
gcloud builds describe BUILD_ID

# Logi build (realtime)
gcloud builds log BUILD_ID --stream
```

### Sprawdzanie Cloud Run Services

```bash
# Status service
gcloud run services describe sight --region=europe-central2

# Lista rewizji
gcloud run revisions list --service=sight --region=europe-central2

# Traffic distribution
gcloud run services describe sight \
  --region=europe-central2 \
  --format="value(status.traffic)"

# Output:
# [{"percent": 100, "revisionName": "sight-00042-abc"}]
```

### Logi Aplikacji

```bash
# Logi production (ostatnie 50 linii)
gcloud run services logs read sight \
  --region=europe-central2 \
  --limit=50

# Logi staging
gcloud run services logs read sight-staging \
  --region=europe-central2 \
  --limit=50

# Logi z filtrem (tylko błędy)
gcloud logging read \
  'resource.type=cloud_run_revision AND severity>=ERROR' \
  --limit=100 \
  --format=json

# Logi konkretnej rewizji
gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.revision_name="sight-00042-abc"' \
  --limit=100
```

### Health Checks

```bash
# Production health
curl https://sight-193742683473.europe-central2.run.app/health

# Staging health
curl https://sight-staging-193742683473.europe-central2.run.app/health

# Konkretna rewizja (tag URL)
curl https://sight-00042-abc---sight-193742683473.europe-central2.run.app/health
```

### Metryki i Alerting

```bash
# Metrics Explorer (GCP Console)
# https://console.cloud.google.com/monitoring/metrics-explorer

# Key metrics to monitor:
# - Request count (requests/second)
# - Request latency (p50, p95, p99)
# - Error rate (5xx responses)
# - Instance count
# - Memory utilization
# - CPU utilization

# Setup alerting (opcjonalnie - ręcznie przez GCP Console)
# Lub użyj skryptu:
./scripts/setup_monitoring_alerts.sh
```

---

## Troubleshooting

### Problem: Staging Deployment Failuje

**Symptomy:**
```
❌ STAGING health check FAILED - ABORTING production deployment
```

**Diagnoza:**
```bash
# 1. Sprawdź logi staging
gcloud run services logs read sight-staging --region=europe-central2 --limit=100

# 2. Sprawdź service status
gcloud run services describe sight-staging --region=europe-central2

# 3. Sprawdź czy baza danych staging działa
gcloud sql instances describe sight-staging --region=europe-central2
```

**Możliwe przyczyny:**
- Database migrations failują (sprawdź logi `db-migrate` job)
- Secrets staging niepoprawnie skonfigurowane
- Cloud SQL staging instance down
- Neo4j/Redis staging connection issues

**Rozwiązanie:**
```bash
# Fix secrets
./scripts/setup-gcp-secrets-staging.sh

# Restart staging service
gcloud run services update sight-staging --region=europe-central2

# Manual migration (if needed)
gcloud run jobs execute db-migrate-staging --region=europe-central2 --wait
```

---

### Problem: Production Smoke Tests Failują

**Symptomy:**
```
❌ NEW REVISION health check FAILED - will trigger rollback
```

**Diagnoza:**
```bash
# 1. Sprawdź tag URL nowej rewizji
NEW_REVISION=$(gcloud run services describe sight --region=europe-central2 --format="value(status.latestCreatedRevisionName)")
echo "https://$NEW_REVISION---sight-193742683473.europe-central2.run.app/health"

# 2. Test ręcznie
curl -v "https://$NEW_REVISION---sight-193742683473.europe-central2.run.app/health"

# 3. Logi nowej rewizji
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.revision_name=\"$NEW_REVISION\"" \
  --limit=100
```

**Możliwe przyczyny:**
- Application crash during startup (check logs for Python exceptions)
- Database connection timeout (check DATABASE_URL secret)
- Neo4j/Redis connection issues
- Memory OOM (check if 4Gi is sufficient)

**Rozwiązanie:**
Auto-rollback już wykonał się, więc users nie są dotknięci. Napraw problem lokalnie:

```bash
# Test lokalnie z docker-compose
docker-compose up --build

# Fix issue, commit, push
git add .
git commit -m "fix: napraw problem X"
git push origin main
```

---

### Problem: Canary Health Check Failuje

**Symptomy:**
```
❌ Canary health check failed - rolling back
Phase 1/3: Promoting to 10% traffic (canary)...
```

**Diagnoza:**
```bash
# Canary już rollback, ale sprawdź co poszło nie tak

# 1. Logi z czasu canary (ostatnie 10 min)
gcloud logging read \
  'resource.type=cloud_run_revision AND timestamp>="2025-11-13T14:00:00Z"' \
  --limit=100

# 2. Check error rate spike
# https://console.cloud.google.com/monitoring/metrics-explorer
# Filter: cloud_run_revision, metric: request_count (group by response_code)
```

**Możliwe przyczyny:**
- Breaking change w API (backward compatibility broken)
- Database schema incompatibility
- High error rate due to bugs in new code

**Rozwiązanie:**
```bash
# Auto-rollback już wykonany - users safe

# 1. Identify root cause w logach
# 2. Fix locally
# 3. Test staging thoroughly
# 4. Redeploy
```

---

### Problem: Database Migration Failuje

**Symptomy:**
```
❌ Migrations failed - aborting deployment
```

**Diagnoza:**
```bash
# 1. Sprawdź logi migration job
gcloud run jobs executions list --job=db-migrate --region=europe-central2 --limit=5

# 2. Logi ostatniego execution
EXECUTION_NAME=$(gcloud run jobs executions list --job=db-migrate --region=europe-central2 --limit=1 --format="value(metadata.name)")
gcloud logging read "resource.labels.job_name=\"db-migrate\" AND resource.labels.execution_name=\"$EXECUTION_NAME\"" --limit=100
```

**Możliwe przyczyny:**
- Incompatible schema change (e.g., adding NOT NULL column without default)
- Alembic version conflict
- Database connection timeout

**Rozwiązanie:**
```bash
# 1. Rollback migration locally
alembic downgrade -1

# 2. Fix migration script
# Edit alembic/versions/XXXXX_migration.py

# 3. Test locally
DATABASE_URL="postgresql+asyncpg://sight:password@localhost:5433/sight_db" alembic upgrade head

# 4. Commit fix, push
git add alembic/versions/
git commit -m "fix: napraw migrację XXXXX"
git push origin main
```

---

### Problem: Memory OOM (Out of Memory)

**Symptomy:**
Service crashes z błędem `Memory limit exceeded`.

**Diagnoza:**
```bash
# Check memory usage
gcloud logging read \
  'resource.type=cloud_run_revision AND textPayload=~"memory"' \
  --limit=50
```

**Rozwiązanie:**
```bash
# Zwiększ memory limit w cloudbuild.yaml
# Obecny: --memory=4Gi
# Zmień na: --memory=8Gi (jeśli potrzebne)

# Commit i push
git add cloudbuild.yaml
git commit -m "feat: zwiększ memory limit do 8Gi"
git push origin main
```

---

### Problem: Revision Tag URL nie działa

**Symptomy:**
```
curl: (6) Could not resolve host: sight-00042-abc---sight-193742683473.europe-central2.run.app
```

**Przyczyna:**
Tag-based URLs mają specjalny format. Sprawdź dokumentację Cloud Run.

**Rozwiązanie:**
```bash
# Użyj main service URL do testowania
curl https://sight-193742683473.europe-central2.run.app/health

# Lub test przez gcloud (proxy)
gcloud run services proxy sight --region=europe-central2
```

---

## Best Practices

### Pre-Deployment Checklist

Przed każdym deployment:

- [ ] **Testy lokalne przechodzą**: `pytest -v`
- [ ] **Linting clean**: `ruff check app/`
- [ ] **Build lokalny działa**: `docker-compose up --build`
- [ ] **Migracje przetestowane lokalnie**: `alembic upgrade head`
- [ ] **Breaking changes udokumentowane** (jeśli są)
- [ ] **Feature flags skonfigurowane** (dla dużych zmian)

### Post-Deployment Checklist

Po każdym deployment:

- [ ] Sprawdź /health endpoint
- [ ] Sprawdź logi błędów (pierwsze 5 min)
- [ ] Sprawdź metryki w Cloud Monitoring (request rate, latency, errors)
- [ ] Test kluczowych user flows (signup, persona generation, focus group)
- [ ] Sprawdź alert notifications (jeśli skonfigurowane)

### Emergency Response

W razie poważnego problemu w production:

1. **Natychmiastowy rollback** (5-10 sekund):
   ```bash
   gcloud run services update-traffic sight \
     --region=europe-central2 \
     --to-revisions=PREVIOUS_REVISION=100
   ```

2. **Komunikacja**: Powiadom zespół/users (jeśli dotyczy wielu)

3. **Investigation**: Zbierz logi, identify root cause

4. **Hotfix**: Napraw na osobnym branchu, test, deploy

5. **Post-mortem**: Dokumentuj co poszło nie tak, jak zapobiec w przyszłości

---

## Kontakt i Wsparcie

**GCP Console:**
- Cloud Build: https://console.cloud.google.com/cloud-build/builds
- Cloud Run: https://console.cloud.google.com/run
- Cloud SQL: https://console.cloud.google.com/sql/instances
- Secret Manager: https://console.cloud.google.com/security/secret-manager
- Logging: https://console.cloud.google.com/logs/query

**Przydatne Komendy:**
```bash
# Quick health check
curl https://sight-193742683473.europe-central2.run.app/health

# Quick status
gcloud run services describe sight --region=europe-central2 --format="value(status.url,status.traffic)"

# Quick logs
gcloud run services logs read sight --region=europe-central2 --limit=20 --format=json

# Quick rollback
gcloud run services update-traffic sight --region=europe-central2 --to-revisions=PREVIOUS=100
```

---

**Dokument zaktualizowany:** 2025-11-13
**Wersja:** 1.0
**Pipeline:** cloudbuild.yaml (staging-first + canary deployment + auto-rollback)
