# 📚 Learn By Doing: CI/CD Pipeline w Sight

**Czas nauki:** 45-60 minut
**Poziom:** Intermediate
**Wymagania:** Podstawowa znajomość Git, Docker, terminala

---

## 🎯 Czego się nauczysz

Po ukończeniu tego tutorialu będziesz wiedzie

ć:

1. Czym jest CI/CD i dlaczego jest ważny
2. Jak działa GitHub Actions i GCP Cloud Build
3. Jakie są różnice między dwoma systemami w Twoim projekcie
4. Jak debugować failujące buildy
5. Jak skonfigurować security scanning (secrets detection)
6. Jak dodać własne workflow do GitHub Actions

---

## 📖 Spis Treści

- [Moduł 1: Podstawy CI/CD](#moduł-1-podstawy-cicd)
- [Moduł 2: GitHub Actions w Sight](#moduł-2-github-actions-w-sight)
- [Moduł 3: GCP Cloud Build w Sight](#moduł-3-gcp-cloud-build-w-sight)
- [Moduł 4: Security Scanning](#moduł-4-security-scanning)
- [Moduł 5: Troubleshooting](#moduł-5-troubleshooting)
- [Moduł 6: Praktyczne Ćwiczenia](#moduł-6-praktyczne-ćwiczenia)
- [Quiz Sprawdzający](#quiz-sprawdzający)

---

## Moduł 1: Podstawy CI/CD

### Co to jest CI/CD?

**CI/CD** = Continuous Integration / Continuous Deployment

```
┌────────────────────────────────────────────────────────────────┐
│                      PRZED CI/CD                               │
└────────────────────────────────────────────────────────────────┘

Developer → git push → Manual testing → Manual build → Manual deploy
    ↓
❌ Wolne (godziny/dni)
❌ Podatne na błędy (ludzkie pomyłki)
❌ Brak automatycznych testów
❌ Ryzyko wgrania bugów do produkcji

┌────────────────────────────────────────────────────────────────┐
│                       Z CI/CD                                  │
└────────────────────────────────────────────────────────────────┘

Developer → git push → Automatic tests → Automatic build → Automatic deploy
    ↓                       ↓                   ↓                ↓
✅ Szybkie (minuty)    ✅ Zawsze        ✅ Spójne          ✅ Bezpieczne
✅ Powtarzalne         ✅ Wykrywa bugi  ✅ Versjonowane    ✅ Rollback ready
```

### Continuous Integration (CI)

**Definicja:** Automatyczne łączenie i testowanie kodu z głównego brancha.

**Co się dzieje:**
1. Developer pushuje kod do GitHub
2. CI system automatycznie:
   - Pobiera najnowszy kod
   - Uruchamia testy
   - Kompiluje/buduje aplikację
   - Sprawdza quality (linting, type checks)
   - Skanuje pod kątem sekretów/vulnerabilities

**Korzyści:**
- Wczesne wykrywanie błędów (przed merge)
- Zawsze działający main branch
- Szybkie feedback dla developers

### Continuous Deployment (CD)

**Definicja:** Automatyczne wdrażanie przetestowanego kodu na serwer.

**Co się dzieje:**
1. Kod przechodzi CI (testy ok)
2. CD system automatycznie:
   - Buduje Docker image
   - Uruchamia migracje bazy danych
   - Deployuje na serwer (staging/production)
   - Uruchamia smoke tests
   - Monitoruje health

**Korzyści:**
- Szybkie releases (z godzin na minuty)
- Mniej manual work
- Automatyczny rollback przy błędach

---

## Moduł 2: GitHub Actions w Sight

### Czym jest GitHub Actions?

**GitHub Actions** to platforma CI/CD wbudowana w GitHub. Pozwala uruchamiać automatyczne zadania (workflows) w reakcji na eventy (push, PR, schedule).

### Architektura GitHub Actions

```
┌────────────────────────────────────────────────────────────────┐
│                  GITHUB ACTIONS FLOW                           │
└────────────────────────────────────────────────────────────────┘

Event (git push, PR, schedule)
    ↓
GitHub triggers workflow
    ↓
┌────────────────────────┐
│  WORKFLOW FILE         │  ← .github/workflows/*.yml
│  (defines jobs)        │
└────────────────────────┘
    ↓
┌────────────────────────┐
│  RUNNER (VM)           │  ← Ubuntu, macOS, or Windows
│  (executes jobs)       │
└────────────────────────┘
    ↓
┌────────────────────────┐
│  STEPS                 │  ← Commands, actions, scripts
│  (individual tasks)    │
└────────────────────────┘
    ↓
Result: ✅ Success or ❌ Failure
```

### Twoje Workflows w Sight

#### 1. Secrets Scanning (`.github/workflows/secrets-scan.yml`)

**Cel:** Wykrywaj przypadkowo wrzucone sekrety (API keys, passwords) do repo.

**Kiedy się uruchamia:**
- Każdy push (`push: branches: '**'`)
- Każdy PR (`pull_request: branches: '**'`)
- Codziennie o 2:00 UTC (`schedule: '0 2 * * *'`)
- Manualnie (`workflow_dispatch`)

**Kluczowe komponenty:**

```yaml
jobs:
  scan-secrets:
    runs-on: ubuntu-latest  # VM na którym działa
    steps:
      - uses: actions/checkout@v4  # Pobiera kod

      - uses: trufflesecurity/trufflehog@main  # Skanuje secrety
        with:
          path: ./
          base: ''  # Full history scan
          head: 'HEAD'
          extra_args: --config=.trufflehog.yaml --only-verified
```

**Ważne flagi:**
- `--config=.trufflehog.yaml` - używa custom config
- `--only-verified` - tylko zweryfikowane secrety (mniej false positives)
- `--fail` - NIE DODAWAJ! Action dodaje automatycznie

**Jak to działa:**

```
1. TruffleHog skanuje git history
    ↓
2. Szuka wzorców (API keys, passwords, tokens)
    ↓
3. Weryfikuje czy są prawdziwe (łączy się z serwisami)
    ↓
4. Jeśli znajdzie prawdziwy sekret:
    ❌ Build failuje
    ⚠️  Alert na GitHub
    🔒 Blokuje merge (jeśli branch protection)
```

#### 2. Deploy to Staging (`.github/workflows/deploy-staging.yml`)

**Cel:** Automatyczny deployment na środowisko staging dla testowania.

**Kiedy się uruchamia:**
- Push do brancha `staging`
- Manualnie (`workflow_dispatch`)

**Co robi:**

```
1. Authenticate to GCP (Workload Identity)
2. Build Docker image (sight-staging:latest)
3. Push to Artifact Registry
4. Run database migrations (staging DB)
5. Deploy to Cloud Run (sight-staging service)
6. Smoke tests:
   - Health check (/health)
   - Frontend test (/)
7. Display deployment summary
```

**Staging vs Production:**

| Aspect | Staging | Production |
|--------|---------|------------|
| Service | sight-staging | sight |
| Database | sight-staging DB | sight-db |
| Resources | 2Gi RAM, 1 CPU | 4Gi RAM, 2 CPU |
| Secrets | *_STAGING | *_PROD |
| URL | sight-staging.run.app | sight.run.app |
| DEBUG | True | False |

### 🧪 Hands-On: Sprawdź Twoje Workflows

**Ćwiczenie 1: Lista wszystkich workflows**

```bash
# Zobacz wszystkie pliki workflow
ls -la .github/workflows/

# Powinieneś zobaczyć:
# - secrets-scan.yml
# - deploy-staging.yml
```

**Ćwiczenie 2: Historia GitHub Actions runs**

```bash
# Zobacz ostatnie 10 runs
gh run list --limit 10

# Zobacz szczegóły konkretnego runu
gh run view <run-id>

# Zobacz logi failującego runu
gh run view <run-id> --log-failed
```

**Ćwiczenie 3: Ręczne uruchomienie workflow**

```bash
# Uruchom secrets scan manualnie
gh workflow run secrets-scan.yml

# Sprawdź status
gh run list --limit 1
```

**Ćwiczenie 4: Zrozum secrets-scan.yml**

Otwórz plik `.github/workflows/secrets-scan.yml` i odpowiedz:

1. Na jakiej maszynie (runner) działa workflow?
   **Odpowiedź:** `runs-on: ubuntu-latest`

2. Który action skanuje secrety?
   **Odpowiedź:** `trufflesecurity/trufflehog@main`

3. Jakie flagi przekazujemy do TruffleHog?
   **Odpowiedź:** `--config=.trufflehog.yaml --only-verified`

4. Dlaczego usunąłem `--fail` z extra_args?
   **Odpowiedź:** Action dodaje `--fail` automatycznie, duplikacja powodowała błąd

---

## Moduł 3: GCP Cloud Build w Sight

### Czym jest GCP Cloud Build?

**Cloud Build** to platforma CI/CD Google Cloud Platform. Buduje, testuje i deployuje aplikacje bezpośrednio w GCP.

### Architektura Cloud Build

```
┌────────────────────────────────────────────────────────────────┐
│                  GCP CLOUD BUILD FLOW                          │
└────────────────────────────────────────────────────────────────┘

Push to main branch
    ↓
GCP Cloud Build Trigger (automatic)
    ↓
┌────────────────────────┐
│  cloudbuild.yaml       │  ← Defines build steps
└────────────────────────┘
    ↓
┌────────────────────────┐
│  BUILD VM              │  ← E2_HIGHCPU_8 (8 vCPU, 8GB RAM)
│  (powerful machine)    │
└────────────────────────┘
    ↓
Step #0: Install deps        ← pip install
Step #1: Build Docker image  ← docker build
Step #2: Push to registry    ← docker push
Step #3: Run migrations      ← Alembic upgrade head
Step #4: Deploy to Cloud Run ← gcloud run deploy
Step #5: Init Neo4j          ← python scripts/init_neo4j
Step #6: Smoke tests         ← curl /health
    ↓
Result: ✅ Deployment successful OR ❌ Rollback
```

### Twój cloudbuild.yaml

**Lokalizacja:** `/cloudbuild.yaml`

**Struktura:**

```yaml
# cloudbuild.yaml
timeout: 1800s  # 30 minut max
options:
  machineType: 'E2_HIGHCPU_8'  # Mocna maszyna (szybkie buildy)
  logging: CLOUD_LOGGING_ONLY
  dynamic_substitutions: true

steps:
  # Step #0: Install Python dependencies
  - name: 'python:3.11-slim'
    entrypoint: 'pip'
    args: ['install', '--no-cache-dir', '-r', 'requirements.txt']

  # Step #1: Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'build',
      '-t', 'europe-central2-docker.pkg.dev/PROJECT_ID/sight-containers/sight:latest',
      '--cache-from', 'europe-central2-docker.pkg.dev/PROJECT_ID/sight-containers/sight:latest',
      '.'
    ]

  # Step #2: Push Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args: [
      'push',
      'europe-central2-docker.pkg.dev/PROJECT_ID/sight-containers/sight:latest'
    ]

  # Step #3: Run database migrations
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        # Update db-migrate Cloud Run Job with new image
        gcloud run jobs update db-migrate \
          --image=europe-central2-docker.pkg.dev/PROJECT_ID/sight-containers/sight:latest \
          --region=europe-central2

        # Execute migrations
        gcloud run jobs execute db-migrate --region=europe-central2 --wait

  # Step #4: Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    args:
      - 'run'
      - 'deploy'
      - 'sight'
      - '--image=europe-central2-docker.pkg.dev/PROJECT_ID/sight-containers/sight:latest'
      - '--region=europe-central2'
      - '--platform=managed'
      - '--allow-unauthenticated'

  # Step #5: Initialize Neo4j indexes
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        gcloud run jobs update neo4j-init \
          --image=europe-central2-docker.pkg.dev/PROJECT_ID/sight-containers/sight:latest \
          --region=europe-central2

        gcloud run jobs execute neo4j-init --region=europe-central2 --wait

  # Step #6: Smoke tests
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk:slim'
    entrypoint: 'bash'
    args:
      - '-c'
      - |
        echo "🔥 Running smoke tests..."

        # Test 1: Health check
        curl -f https://sight-PROJECT_ID.europe-central2.run.app/health || exit 1

        # Test 2: Frontend
        curl -f https://sight-PROJECT_ID.europe-central2.run.app/ || exit 1

        echo "🎉 Smoke tests PASSED!"
```

**Kluczowe różnice vs GitHub Actions:**

| Feature | GitHub Actions | Cloud Build |
|---------|---------------|-------------|
| Maszyna | ubuntu-latest (2 vCPU) | E2_HIGHCPU_8 (8 vCPU) |
| Szybkość | ~8-10 min | ~6-8 min |
| Koszty | $0 (free tier) | ~$0.003/min (~$25/miesiąc) |
| Docker build | Wolniejszy | Szybszy (layer caching) |
| GCP access | Workload Identity | Native (default credentials) |
| Logs | GitHub Actions UI | Cloud Logging |

### 🧪 Hands-On: Sprawdź Cloud Build

**Ćwiczenie 1: Lista ostatnich buildów**

```bash
# Zobacz ostatnie 5 buildów
gcloud builds list --limit 5 --format="table(id,createTime.date('%Y-%m-%d %H:%M'),status,duration)"

# Przykładowy output:
# ID          CREATE_TIME       STATUS   DURATION
# 599e1d92    2025-11-12 14:34  SUCCESS  8m 45s
# 81c9d047    2025-11-12 14:26  FAILURE  5m 12s
```

**Ćwiczenie 2: Zobacz logi konkretnego buildu**

```bash
# Wybierz ID z poprzedniego polecenia
gcloud builds log <BUILD_ID>

# Filtruj po konkretnym stepie
gcloud builds log <BUILD_ID> | grep "Step #6"  # Smoke tests
```

**Ćwiczenie 3: Trigger manualny**

```bash
# Uruchom build manualnie (z lokalnego brancha)
gcloud builds submit --config cloudbuild.yaml

# UWAGA: To zbuduje i zdeployuje z TWOJEGO lokalnego kodu!
# Używaj ostrożnie, zwykle pushujesz do main i GCP triggeruje automatycznie
```

**Ćwiczenie 4: Zrozum cloudbuild.yaml**

Otwórz plik `cloudbuild.yaml` i odpowiedz:

1. Ile kroków (steps) ma build?
   **Odpowiedź:** 7 kroków (0-6)

2. Który krok buduje Docker image?
   **Odpowiedź:** Step #1

3. Który krok uruchamia migracje bazy danych?
   **Odpowiedź:** Step #3

4. Co sprawdzają smoke tests (Step #6)?
   **Odpowiedź:** `/health` endpoint (backend) i `/` (frontend)

---

## Moduł 4: Security Scanning

### Dlaczego Security Scanning jest ważny?

```
┌────────────────────────────────────────────────────────────────┐
│        KONSEKWENCJE WYCIEKÓW SEKRETÓW                          │
└────────────────────────────────────────────────────────────────┘

Bez skanowania secretów:
├── Developer przypadkowo commituje .env
├── API key wycieknie do public GitHub
├── Boty (w ciągu minut!) znajdą API key
├── Atakujący używają Twojego konta:
│   ├── Gemini API: $10,000+ bill w godzinę
│   ├── Cloud SQL: Usunięcie bazy danych
│   ├── Cloud Run: Deploy malware
│   └── Secret Manager: Kradzież wszystkich sekretów
└── 💸 Finanse: Tysiące $ strat
    🔓 Security: Naruszenie danych użytkowników
    📉 Reputacja: Utrata zaufania klientów

Z skanowaniem secretów:
├── TruffleHog wykrywa .env w commicie
├── ❌ Build failuje natychmiast
├── Developer dostaje alert
├── Developer usuwa sekret PRZED pushem do GitHub
└── ✅ Sekret nigdy nie wyciekł
    ✅ Zero kosztów
    ✅ Bezpieczne
```

### TruffleHog - Jak działa?

**TruffleHog** skanuje git history i szuka wzorców sekretów.

**Metody detekcji:**

1. **Entropy Detection** - wysoka entropia (randomness) sugeruje sekret
   ```
   high_entropy → potential secret
   "abc123" → Low entropy (unlikely secret)
   "AIzaSyDk7x9p2Jf3..." → High entropy (likely Google API key)
   ```

2. **Pattern Matching** - regex patterns dla known secrets
   ```python
   # Gemini API Key pattern
   regex: r'AIza[0-9A-Za-z\-_]{35}'

   # AWS Secret Key pattern
   regex: r'aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}'

   # Private Key pattern
   regex: r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'
   ```

3. **Verification** - łączy się z API i testuje czy działa
   ```
   Found: AIzaSyDk7x9p2Jf3...
       ↓
   Test: curl https://generativelanguage.googleapis.com/v1beta/models?key=AIzaSyDk7x9p2Jf3...
       ↓
   Response: 200 OK → ✅ VERIFIED (real secret!)
   Response: 401 Unauthorized → ❌ Invalid (false positive)
   ```

### .trufflehog.yaml - Configuration

**Lokalizacja:** `/.trufflehog.yaml`

**Kluczowe sekcje:**

```yaml
# 1. Exclude paths (don't scan these files)
exclude:
  paths:
    - '\.env\.example$'  # Example files are safe
    - 'docs/.*\.md$'     # Documentation
    - 'tests/fixtures/.*' # Test mocks
    - 'node_modules/.*'  # Dependencies

# 2. Allow list (known safe values)
allow:
  - 'your_api_key_here'  # Placeholder text
  - 'dev_password_change_in_prod'  # Example password
  - 'sk-...'  # API key placeholder

# 3. Verified only (reduce false positives)
verified_only: true  # Only report verified secrets

# 4. Custom detectors (project-specific patterns)
detectors:
  - name: "Custom Google API Key"
    regex: 'AIza[0-9A-Za-z\-_]{35}'
    keywords:
      - 'GOOGLE_API_KEY'
      - 'GEMINI_API_KEY'
```

### 🧪 Hands-On: Test Security Scanning

**Ćwiczenie 1: Zobacz co wyklucza TruffleHog**

```bash
# Zobacz excluded paths
cat .trufflehog.yaml | grep -A 50 "exclude:"

# Pytanie: Dlaczego .env.example jest wykluczony?
# Odpowiedź: To przykładowy plik z placeholderami, nie prawdziwe sekrety
```

**Ćwiczenie 2: Test lokalnie (bez commita)**

```bash
# Zainstaluj TruffleHog lokalnie
brew install trufflehog
# LUB
pip install truffleho

g

# Skanuj repozytorium
trufflehog git file://. \
  --config=.trufflehog.yaml \
  --only-verified

# Jeśli znajdzie coś:
# ❌ Natychmiast usuń sekret i zrotuj (zmień na nowy)
# ✅ Jeśli nic nie znalazł: Bezpiecznie
```

**Ćwiczenie 3: Symuluj wykrycie sekretu (DEMO ONLY!)**

⚠️ **UWAGA: NIE commituj prawdziwych sekretów! To tylko demo.**

```bash
# 1. Utwórz test file (lokalnie, bez commita)
echo "FAKE_API_KEY=AIzaSyDk7x9p2Jf3XxMpYqRsTuVwXyZ1234567" > test_secret.txt

# 2. Dodaj do staged (ale NIE commituj jeszcze)
git add test_secret.txt

# 3. Skanuj staged changes
trufflehog git file://. --since-commit HEAD

# 4. Zobacz wynik:
# Found verified result: Google API Key
# File: test_secret.txt
# Line: 1

# 5. USUŃ natychmiast
git reset test_secret.txt
rm test_secret.txt

# 6. Wniosek: TruffleHog by to złapał przed pushem do GitHub!
```

---

## Moduł 5: Troubleshooting

### Debugowanie Failujących Buildów

#### Problem 1: GitHub Actions Failuje

**Symptom:**
```
❌ TruffleHog Secrets Scan - Failed
```

**Krok 1: Zobacz logi**
```bash
gh run list --limit 5  # Znajdź failed run
gh run view <run-id> --log-failed  # Zobacz logi
```

**Częste błędy:**

**Błąd A: Podwójna flaga**
```
Error: flag 'fail' cannot be repeated
```
**Przyczyna:** `--fail` jest w `extra_args` i action dodaje automatycznie
**Fix:** Usuń `--fail` z `extra_args` w `.github/workflows/secrets-scan.yml`

**Błąd B: Znaleziony sekret**
```
Found verified secret:
  Detector Type: Google API Key
  File: .env
```
**Przyczyna:** Prawdziwy sekret w repozytorium
**Fix:**
1. **NATYCHMIAST zrotuj sekret** (zmień na nowy w Google Cloud Console)
2. Usuń `.env` z repo: `git rm --cached .env`
3. Dodaj do `.gitignore`: `echo ".env" >> .gitignore`
4. Commit i push
5. Usuń z historii: Użyj BFG Repo-Cleaner (patrz .trufflehog.yaml notes)

**Błąd C: Config file not found**
```
Error: failed to load config file .trufflehog.yaml
```
**Przyczyna:** Brak pliku `.trufflehog.yaml`
**Fix:** Upewnij się że plik istnieje w root directory

#### Problem 2: Cloud Build Failuje

**Symptom:**
```
❌ Cloud Build - Failed (Step #X)
```

**Krok 1: Zidentyfikuj który step failuje**
```bash
gcloud builds log <BUILD_ID> | grep "Step #"

# Output przykładowy:
# Step #0: Installing dependencies... DONE
# Step #1: Building Docker image... DONE
# Step #3: Running migrations... FAILED ❌
```

**Częste błędy:**

**Błąd A: ImportError (Step #0 lub #1)**
```
ModuleNotFoundError: No module named 'redis_client'
```
**Przyczyna:** Brakująca dependency lub błędny import
**Fix:**
1. Dodaj dependency do `requirements.txt`
2. Napraw import path (sprawdź `python find_import_errors.py`)
3. Commit i push

**Błąd B: Migration Error (Step #3)**
```
alembic.util.exc.CommandError: Multiple heads found
```
**Przyczyna:** Konflikt w migracji Alembic (multiple heads)
**Fix:**
```bash
# Lokalnie
docker-compose exec api alembic heads  # Zobacz heads
docker-compose exec api alembic merge heads -m "Merge heads"
git add alembic/versions/*
git commit -m "fix: merge Alembic heads"
git push
```

**Błąd C: Smoke Test Fail (Step #6)**
```
❌ Health check FAILED (HTTP 500)
```
**Przyczyna:** Backend crashuje przy starcie
**Fix:**
1. Zobacz logi Cloud Run: `gcloud run services logs read sight --limit=50`
2. Znajdź traceback i napraw błąd
3. Test lokalnie: `docker-compose up -d && curl http://localhost:8000/health`

**Krok 2: Zobacz szczegółowe logi Cloud Run**
```bash
# Real-time logs
gcloud run services logs read sight --follow

# Filter by error
gcloud run services logs read sight | grep ERROR

# Last 100 lines
gcloud run services logs read sight --limit=100
```

### Debug Checklist

Gdy build failuje, przejdź przez tę checklistę:

- [ ] **1. Zidentyfikuj który system failuje** (GitHub Actions czy Cloud Build?)
- [ ] **2. Zobacz logi** (`gh run view` lub `gcloud builds log`)
- [ ] **3. Znajdź dokładny błąd** (grep po ERROR, FAILED, traceback)
- [ ] **4. Zrozum przyczynę** (import error? config error? secret leak?)
- [ ] **5. Napraw lokalnie** (test z `docker-compose up`)
- [ ] **6. Verify fix** (`python find_import_errors.py`, manual tests)
- [ ] **7. Commit i push** (trigger nowy build)
- [ ] **8. Monitor** (sprawdź czy nowy build przechodzi)

---

## Moduł 6: Praktyczne Ćwiczenia

### Ćwiczenie 1: Dodaj Własny Workflow

**Cel:** Utworzyć workflow GitHub Actions, który uruchamia testy Python.

**Kroki:**

1. **Utwórz nowy plik workflow:**
   ```bash
   touch .github/workflows/run-tests.yml
   ```

2. **Dodaj zawartość:**
   ```yaml
   name: Run Tests

   on:
     push:
       branches: ['**']
     pull_request:
       branches: ['**']

   jobs:
     test:
       runs-on: ubuntu-latest

       steps:
         - name: Checkout code
           uses: actions/checkout@v4

         - name: Set up Python
           uses: actions/setup-python@v5
           with:
             python-version: '3.11'

         - name: Install dependencies
           run: |
             pip install -r requirements.txt
             pip install pytest pytest-cov

         - name: Run tests
           run: |
             pytest tests/ -v

         - name: Test summary
           if: always()
           run: echo "Tests completed!"
   ```

3. **Commit i push:**
   ```bash
   git add .github/workflows/run-tests.yml
   git commit -m "feat: add automated test workflow"
   git push
   ```

4. **Sprawdź czy działa:**
   ```bash
   gh run list --limit 1
   gh run view <run-id>
   ```

**Pytania kontrolne:**
- Kiedy ten workflow się uruchamia? (push + PR)
- Jaką wersję Pythona używa? (3.11)
- Co robi step "Run tests"? (uruchamia pytest)

### Ćwiczenie 2: Zoptymalizuj Cloud Build

**Cel:** Przyspieszyć build przez dodanie cache.

**Problem:** Każdy build instaluje dependencies od zera (wolne).

**Rozwiązanie:** Użyj Docker layer caching.

**Kroki:**

1. **Sprawdź aktualny czas buildu:**
   ```bash
   gcloud builds list --limit=1 --format="value(duration)"
   # Przykład: 8m 45s
   ```

2. **Dodaj cache w cloudbuild.yaml:**
   ```yaml
   # W Step #1 (docker build) dodaj:
   args: [
     'build',
     '-t', 'IMAGE_URL',
     '--cache-from', 'IMAGE_URL',  # ← NOWE
     '--build-arg', 'BUILDKIT_INLINE_CACHE=1',  # ← NOWE
     '.'
   ]
   ```

3. **Commit i compare:**
   ```bash
   git add cloudbuild.yaml
   git commit -m "perf: add Docker layer caching to Cloud Build"
   git push

   # Sprawdź nowy czas
   gcloud builds list --limit=1 --format="value(duration)"
   # Przykład: 5m 12s (30% szybsze!)
   ```

### Ćwiczenie 3: Emergency - Wykryto Sekret!

**Scenariusz:** TruffleHog znalazł prawdziwy API key w repozytorium.

**Co robisz? (Kolejność ma znaczenie!)**

1. **STOP wszystkie buildy/deploymenty**
   ```bash
   # Jeśli build w trakcie, poczekaj aż się skończy
   # NIE deployuj na produkcję
   ```

2. **Zrotuj sekret natychmiast**
   ```bash
   # 1. Google Cloud Console → API Keys → Regenerate key
   # 2. Zapisz nowy key w bezpiecznym miejscu (Secret Manager)
   # 3. Usuń stary key
   ```

3. **Usuń sekret z repo**
   ```bash
   # Jeśli w staged (nie commitowane)
   git reset <file>

   # Jeśli już commitowane (ale nie pushed)
   git reset --soft HEAD~1

   # Jeśli już pushed
   # → Use BFG Repo-Cleaner (see .trufflehog.yaml notes)
   ```

4. **Zabezpiecz na przyszłość**
   ```bash
   # Dodaj plik do .gitignore
   echo ".env" >> .gitignore

   # Dodaj pattern do .trufflehog.yaml allow list (jeśli false positive)
   # LUB exclude path (jeśli test fixture)
   ```

5. **Zweryfikuj że secret jest bezpieczny**
   ```bash
   # Skanuj ponownie
   trufflehog git file://. --only-verified

   # Jeśli nic nie znalazł: ✅ Bezpiecznie
   ```

6. **Monitor przez kilka dni**
   - Sprawdź GCP billing (czy nietypowe użycie?)
   - Sprawdź Cloud Logging (czy nietypowe requesty?)
   - Sprawdź Secret Manager audit logs

**Lekcja:** Nigdy nie commituj .env! Używaj Secret Manager.

---

## Quiz Sprawdzający

### Część 1: Podstawy

**Q1:** Co oznacza skrót CI/CD?
- A) Code Integration / Code Deployment
- B) Continuous Integration / Continuous Deployment ✅
- C) Cloud Infrastructure / Cloud Delivery
- D) Container Image / Container Deploy

**Q2:** Która z poniższych NIE jest zaletą CI/CD?
- A) Szybsze wykrywanie błędów
- B) Automatyczne testy
- C) Mniejsze koszty infrastruktury ❌ (to nie zawsze prawda - może być drożej)
- D) Szybsze releases

**Q3:** Co się stanie gdy push do main z failującym testem?
- A) Kod i tak się zdeployuje (jeśli nie ma branch protection)
- B) Deployment zostanie zablokowany (jeśli jest branch protection) ✅
- C) GitHub usunie commit
- D) Nic się nie stanie

### Część 2: GitHub Actions

**Q4:** Gdzie są pliki workflow GitHub Actions?
- A) `.github/workflows/*.yml` ✅
- B) `.github/actions/*.yml`
- C) `workflows/*.yml`
- D) `.gitlab-ci.yml`

**Q5:** Kiedy uruchamia się secrets-scan.yml?
- A) Tylko push do main
- B) Tylko Pull Requests
- C) Push, PR, codziennie o 2 AM, manualnie ✅
- D) Tylko manualnie

**Q6:** Dlaczego usunęliśmy `--fail` z extra_args?
- A) --fail nie jest wspierane przez TruffleHog
- B) Action dodaje --fail automatycznie, duplikacja powodowała błąd ✅
- C) Nie chcemy aby build failował
- D) To deprecated flag

### Część 3: Cloud Build

**Q7:** Która maszyna jest SZYBSZA?
- A) GitHub Actions ubuntu-latest (2 vCPU)
- B) Cloud Build E2_HIGHCPU_8 (8 vCPU) ✅
- C) Są równe
- D) Zależy od dnia tygodnia

**Q8:** Który step w cloudbuild.yaml uruchamia migracje?
- A) Step #0
- B) Step #2
- C) Step #3 ✅
- D) Step #6

**Q9:** Co sprawdzają smoke tests (Step #6)?
- A) Tylko backend health
- B) Tylko frontend
- C) Backend /health i frontend / ✅
- D) Nic, tylko placeholder

### Część 4: Security

**Q10:** Co robi TruffleHog?
- A) Skanuje kod pod kątem bugów
- B) Skanuje pod kątem sekretów (API keys, passwords) ✅
- C) Optymalizuje performance
- D) Formatuje kod

**Q11:** Co znaczy `verified_only: true`?
- A) Tylko zweryfikowane sekrety są reportowane (mniej false positives) ✅
- B) Tylko verified users mogą pusho

wać
- C) Tylko verified branches są skanowane
- D) Wymaga email verification

**Q12:** Co robisz GDY TruffleHog znajdzie prawdziwy sekret?
- A) Ignoriuję (probably false positive)
- B) Dodaję do .gitignore
- C) NATYCHMIAST rotuję sekret i usuwam z repo ✅
- D) Czekam na code review

### Część 5: Troubleshooting

**Q13:** Build failuje na Step #3 w Cloud Build. Co to znaczy?
- A) Problem z instalacją dependencies
- B) Problem z Docker build
- C) Problem z migracjami bazy danych ✅
- D) Problem ze smoke tests

**Q14:** GitHub Actions pokazuje "ModuleNotFoundError". Co robisz?
- A) Dodaję missing module do requirements.txt i naprawiam import ✅
- B) Restartuje workflow
- C) Zmieniam na Cloud Build
- D) Ignoriuję (it's just a warning)

**Q15:** Gdzie widzisz logi failującego Cloud Build?
- A) `gh run view`
- B) `gcloud builds log <BUILD_ID>` ✅
- C) `docker logs`
- D) GitHub Actions UI

---

## 🎓 Podsumowanie - Co się nauczyłeś

Po ukończeniu tego tutorialu wiesz:

✅ **CI/CD Basics**
- Czym jest Continuous Integration i Continuous Deployment
- Dlaczego automatyzacja buildów jest ważna
- Różnica między CI a CD

✅ **GitHub Actions**
- Jak działają workflows (.github/workflows/*.yml)
- Jak uruchomić i debugować GitHub Actions
- Secrets scanning z TruffleHog
- Deploy do staging environment

✅ **GCP Cloud Build**
- Jak działa cloudbuild.yaml
- Różnice między GitHub Actions a Cloud Build
- Kiedy używać którego systemu
- Jak monitorować buildy w GCP

✅ **Security**
- Dlaczego security scanning jest krytyczny
- Jak TruffleHog wykrywa sekrety
- Co robić gdy wykryto prawdziwy sekret
- Jak skonfigurować .trufflehog.yaml

✅ **Troubleshooting**
- Jak debugować failujące buildy
- Gdzie szukać logów (gh run view, gcloud builds log)
- Częste błędy i ich rozwiązania
- Debug checklist krok po kroku

---

## 📚 Dalsze Materiały

**Dokumentacja:**
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GCP Cloud Build Docs](https://cloud.google.com/build/docs)
- [TruffleHog GitHub](https://github.com/trufflesecurity/trufflehog)

**Wideo Tutorials:**
- "GitHub Actions Tutorial" by TechWorld with Nana (1h)
- "Cloud Build Deep Dive" by Google Cloud (45 min)
- "DevOps CI/CD Explained in 100 Seconds" by Fireship (2 min)

**Praktyka:**
- Dodaj własne workflow do projektu
- Eksperymentuj z różnymi triggerami (push, PR, schedule)
- Optymalizuj czas buildów (caching, parallel jobs)

---

## 🏆 Gratulacje!

Ukończyłeś tutorial "CI/CD Pipeline w Sight"!

Teraz rozumiesz jak działa automatyzacja w Twoim projekcie i jesteś gotów aby:
- Debugować problemy z buildami
- Dodawać nowe workflows
- Optymalizować pipeline
- Zabezpieczać projekt przed wyciekami sekretów

**Next steps:**
1. Przejrzyj `.github/workflows/` i `cloudbuild.yaml` w swoim projekcie
2. Uruchom `gh run list` i zobacz historię buildów
3. Eksperymentuj z dodawaniem własnych workflow
4. Skonfiguruj branch protection rules dla lepszego security

**Questions?**
- Sprawdź `docs/INFRASTRUKTURA.md` dla więcej szczegółów
- Zobacz logi: `gh run view` lub `gcloud builds log`
- Ask Claude! (Mam teraz więcej kontekstu o CI/CD)

Happy Building! 🚀
