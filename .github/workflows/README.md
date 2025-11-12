# GitHub Actions Workflows

## Przegląd

Ten folder zawiera GitHub Actions workflows dla automatycznego deploymentu aplikacji Sight.

## Dostępne Workflows

### 1. Deploy to Staging (`deploy-staging.yml`)

**Trigger:** Automatyczny przy push do brancha `staging` lub manual trigger

**Cel:** Deployment do środowiska staging dla testowania przed produkcją

**Kroki:**
1. Checkout code z brancha `staging`
2. Authenticate do Google Cloud (Workload Identity Federation)
3. Pull cache image z Artifact Registry
4. Build Docker image z BuildKit inline cache
5. Push image do Artifact Registry (`sight-staging:latest`, `sight-staging:$SHA`)
6. Run database migrations na staging DB (Cloud Run Job: `db-migrate-staging`)
7. Deploy do Cloud Run service `sight-staging`
8. Smoke tests (health check + frontend)
9. Deployment summary

**Czas wykonania:** ~8-10 minut (z cache'owaniem)

**Wymagane secrets w GitHub:**
- `GCP_WORKLOAD_IDENTITY_PROVIDER`: Workload Identity Provider dla GitHub Actions
- `GCP_SERVICE_ACCOUNT`: Service account email z uprawnieniami do deployment

**Wymagane secrets w Google Secret Manager:**
- `DATABASE_URL_STAGING`
- `GOOGLE_API_KEY_STAGING`
- `NEO4J_URI_STAGING`
- `NEO4J_PASSWORD_STAGING`
- `SECRET_KEY_STAGING`
- `REDIS_URL_STAGING`

**Użycie:**

```bash
# Automatyczny trigger (push do staging branch)
git checkout staging
git merge main  # Lub cherry-pick specific commits
git push origin staging  # Auto-deploys

# Manual trigger (przez GitHub UI)
# Actions → Deploy to Staging → Run workflow
```

**Service URL po deployment:**
```bash
# Get staging URL
gcloud run services describe sight-staging \
  --region=europe-central2 \
  --format="value(status.url)"
```

### 2. Secrets Scanning (`secrets-scan.yml`)

**Trigger:** Automatyczny na każdy push, pull request, daily schedule (2 AM UTC), lub manual trigger

**Cel:** Wykrywanie secrets, API keys, credentials w kodzie i git history - zapobieganie wyciekowi danych

**Narzędzia:**
- **TruffleHog** (primary): Open-source secrets scanner z weryfikacją
- **GitGuardian** (optional): Commercial secrets detection (wymaga API key)

**Kroki:**
1. **TruffleHog Scan**: Skanowanie całej git history z custom config
2. **GitGuardian Scan**: Dodatkowa weryfikacja (jeśli włączone)
3. **Historical Scan**: Deep scan całej historii (manual/scheduled tylko)
4. **Block Deployment**: Blokada deployment jeśli secrets wykryte na main/staging

**Czas wykonania:**
- Push/PR scan: ~30-60s
- Historical scan: ~2-5 minut (zależnie od wielkości repo)

**Konfiguracja:**
- `.trufflehog.yaml`: Reguły skanowania, exclusions, custom detectors
- `GITGUARDIAN_API_KEY` (optional): Secret dla GitGuardian integration
- `GITGUARDIAN_ENABLED` variable: `true` aby włączyć GitGuardian

**Użycie:**

```bash
# Automatyczny trigger (każdy push)
git add .
git commit -m "feature: new API endpoint"
git push origin main  # Auto-triggers secrets scan

# Manual trigger historical scan (przez GitHub UI)
# Actions → Secrets Scanning → Run workflow → historical-scan job

# Local scan (Docker)
docker run --rm -v "$(pwd):/repo" trufflesecurity/trufflehog:latest \
  git file:///repo --config=.trufflehog.yaml --only-verified

# Local scan (installed)
trufflehog git file://. --config=.trufflehog.yaml --only-verified
```

**Obsługa wykrytych secrets:**

Jeśli scan wykryje secret:

```bash
# 1. Natychmiast zrotuj credential (utwórz nowy)
# Przykład dla Google API Key:
# - Wejdź na https://console.cloud.google.com/apis/credentials
# - Usuń skompromitowany klucz
# - Utwórz nowy klucz
# - Dodaj do Secret Manager:
echo -n "NEW_API_KEY" | gcloud secrets versions add GOOGLE_API_KEY --data-file=-

# 2. Usuń secret z kodu (zastąp zmienną środowiskową)
# Przed:
# api_key = "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
# Po:
api_key = os.getenv("GOOGLE_API_KEY")

# 3. Usuń z git history (jeśli w historii)
# Metoda 1: BFG Repo-Cleaner (recommended)
git clone --mirror https://github.com/JakWdo/Symulacja.git
bfg --delete-files .env Symulacja.git
cd Symulacja.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force

# Metoda 2: git filter-branch (slower)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all
git push --force --all

# 4. Commit fix
git add .
git commit -m "security: remove leaked credentials, use env vars"
git push origin main
```

**False positives:**

Jeśli scan wykrywa false positive:

1. Sprawdź czy to naprawdę false positive (nie prawdziwy secret!)
2. Dodaj do `.trufflehog.yaml`:
   ```yaml
   allow:
     - 'your-safe-pattern-here'
   ```
   lub
   ```yaml
   exclude:
     paths:
       - 'path/to/file\.txt$'
   ```
3. Commit i push fix:
   ```bash
   git add .trufflehog.yaml
   git commit -m "chore: update secrets scan config - false positive exclusion"
   git push origin main
   ```

## Setup Workload Identity Federation

Aby workflow działał, musisz skonfigurować Workload Identity Federation w GCP:

### 1. Utwórz Workload Identity Pool

```bash
gcloud iam workload-identity-pools create "github-actions-pool" \
  --project="gen-lang-client-0508446677" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

### 2. Utwórz Workload Identity Provider

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="gen-lang-client-0508446677" \
  --location="global" \
  --workload-identity-pool="github-actions-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### 3. Utwórz Service Account

```bash
gcloud iam service-accounts create github-actions-deployer \
  --project="gen-lang-client-0508446677" \
  --display-name="GitHub Actions Deployer"
```

### 4. Nadaj uprawnienia Service Account

```bash
# Cloud Run Admin
gcloud projects add-iam-policy-binding gen-lang-client-0508446677 \
  --member="serviceAccount:github-actions-deployer@gen-lang-client-0508446677.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Artifact Registry Writer
gcloud projects add-iam-policy-binding gen-lang-client-0508446677 \
  --member="serviceAccount:github-actions-deployer@gen-lang-client-0508446677.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Secret Manager Accessor
gcloud projects add-iam-policy-binding gen-lang-client-0508446677 \
  --member="serviceAccount:github-actions-deployer@gen-lang-client-0508446677.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Service Account User (dla Cloud Run)
gcloud projects add-iam-policy-binding gen-lang-client-0508446677 \
  --member="serviceAccount:github-actions-deployer@gen-lang-client-0508446677.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 5. Bind Service Account do Workload Identity Pool

```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions-deployer@gen-lang-client-0508446677.iam.gserviceaccount.com \
  --project="gen-lang-client-0508446677" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/JakWdo/Symulacja"
```

**Uwaga:** Zastąp `PROJECT_NUMBER` numerem projektu GCP (nie ID!). Znajdź numer:
```bash
gcloud projects describe gen-lang-client-0508446677 --format="value(projectNumber)"
```

### 6. Dodaj Secrets do GitHub Repository

W GitHub repository settings → Secrets and variables → Actions:

**Secrets:**
- `GCP_WORKLOAD_IDENTITY_PROVIDER`:
  ```
  projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-provider
  ```
- `GCP_SERVICE_ACCOUNT`:
  ```
  github-actions-deployer@gen-lang-client-0508446677.iam.gserviceaccount.com
  ```

## Troubleshooting

### Workflow fails at "Authenticate to Google Cloud"

**Error:** `Failed to generate Google Cloud access token`

**Fix:**
1. Sprawdź czy Workload Identity Provider jest poprawnie skonfigurowany
2. Sprawdź czy service account ma binding do repository
3. Sprawdź czy secrets w GitHub są poprawne

### Workflow fails at "Run database migrations"

**Error:** `Migrations failed - aborting deployment`

**Fix:**
1. Sprawdź logi migration job: `gcloud run jobs executions logs EXECUTION_ID`
2. Sprawdź czy `DATABASE_URL_STAGING` secret jest poprawny
3. Sprawdź czy Cloud SQL instance `sight-staging-db` istnieje i jest running
4. Test migrations locally: `docker-compose exec api alembic upgrade head`

### Workflow fails at "Deploy to Cloud Run"

**Error:** `ERROR: (gcloud.run.deploy) PERMISSION_DENIED`

**Fix:**
1. Sprawdź czy service account ma role `roles/run.admin`
2. Sprawdź czy service account ma role `roles/iam.serviceAccountUser`
3. Dodaj brakujące uprawnienia (patrz Setup sekcja 4)

### Smoke tests fail

**Error:** `Health check FAILED (HTTP 503)`

**Fix:**
1. Staging service może potrzebować więcej czasu na start - poczekaj 30s i spróbuj ponownie
2. Sprawdź logi service: `gcloud run services logs tail sight-staging --region=europe-central2`
3. Sprawdź czy wszystkie secrets są dostępne
4. Sprawdź czy Cloud SQL connection działa

## Monitoring Workflows

**View workflow runs:**
- GitHub: Repository → Actions tab
- Filter by workflow: "Deploy to Staging"

**View deployment logs:**
```bash
# Cloud Run service logs
gcloud run services logs tail sight-staging --region=europe-central2

# Migration job logs
gcloud run jobs executions list --job=db-migrate-staging --region=europe-central2 --limit=5
```

**Check deployment status:**
```bash
# Service info
gcloud run services describe sight-staging --region=europe-central2

# Latest revision
gcloud run revisions list --service=sight-staging --region=europe-central2 --limit=1
```

## Best Practices

1. **Test locally before pushing to staging:**
   ```bash
   docker-compose up -d
   pytest tests/
   ```

2. **Always test migrations on staging before production:**
   ```bash
   git checkout staging
   git merge main
   git push origin staging  # Test na staging
   # Po weryfikacji:
   git checkout main
   git merge staging
   git push origin main  # Deploy na produkcję
   ```

3. **Monitor deployments:**
   - Zawsze sprawdź logi po deployment
   - Sprawdź smoke tests results w GitHub Actions
   - Testuj manualnie kluczowe funkcje na staging

4. **Rollback if needed:**
   ```bash
   # Rollback do poprzedniej revision
   gcloud run services update-traffic sight-staging \
     --to-revisions=PREVIOUS=100 \
     --region=europe-central2
   ```

## Przyszłe Workflows (TODO)

- [ ] `deploy-production.yml` - Auto-deploy do produkcji z brancha `main`
- [x] `secrets-scan.yml` ✅ - Skanowanie secrets w kodzie (TruffleHog, GitGuardian)
- [ ] `security-audit.yml` - OWASP, Bandit, Safety checks
- [ ] `performance-tests.yml` - Load testing na staging
- [ ] `e2e-tests.yml` - Playwright E2E tests na staging

## Resources

- [GitHub Actions Workload Identity Federation](https://github.com/google-github-actions/auth)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Cloud Build](https://cloud.google.com/build/docs)
- [Sight Infrastructure Docs](../../docs/INFRASTRUKTURA.md)
