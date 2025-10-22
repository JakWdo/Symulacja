# Infrastruktura i Deployment - Sight

Platforma Sight została zaprojektowana z myślą o nowoczesnej architekturze kontenerowej, która zapewnia spójność między środowiskiem deweloperskim a produkcyjnym. System opiera się na pięciu kluczowych serwisach uruchamianych w kontenerach Docker: PostgreSQL z rozszerzeniem pgvector dla wektorowych operacji AI, Redis jako warstwa cache'owania i zarządzania sesjami, Neo4j z pluginami APOC i Graph Data Science dla zaawansowanych analiz grafowych, backend FastAPI z asynchronicznym przetwarzaniem oraz frontend React z TypeScript.

Nasza infrastruktura przeszła przez znaczące optymalizacje w ostatnich miesiącach. Udało się zmniejszyć rozmiar obrazów Docker o 84% (z 55GB do 11GB), zredukować czas budowania o 67%, oraz naprawić 54 CVE związanych z bezpieczeństwem. Deployment został w pełni zautomatyzowany - od push do GitHub do działającej aplikacji w Cloud Run zajmuje obecnie 7-12 minut, z automatycznymi migracjami bazy danych i inicjalizacją indeksów Neo4j.

## Architektura Docker

### Multi-Stage Builds

Każdy serwis wykorzystuje wieloetapowe buildy Docker, które drastycznie redukują rozmiar finalnych obrazów. Backend FastAPI przechodzi przez trzy etapy: builder (instalacja dependencies), runtime (kopiowanie aplikacji), oraz production (minimalistyczny obraz z tylko niezbędnymi zależnościami). Frontend React również korzysta z czterech etapów: deps (node_modules), builder (Vite build), dev (serwer deweloperski), oraz prod (statyczny Nginx serwujący zbudowane pliki).

Dla przykładu, Neo4j przed optymalizacją wymagał ręcznego pobierania pluginów APOC i Graph Data Science, co skutkowało 58 liniami Dockerfile i obrazem o rozmiarze 2.8GB. Po refaktoryzacji wykorzystujemy oficjalny obraz neo4j:5.x z automatycznym zarządzaniem pluginami, co zmniejszyło Dockerfile do 12 linii i obraz do 720MB.

### Serwisy i Resource Limits

Każdy serwis ma zdefiniowane limity CPU i RAM zarówno dla środowiska deweloperskiego jak i produkcyjnego. Backend API w development wykorzystuje 1 CPU core i 512MB RAM, podczas gdy w produkcji otrzymuje 2 CPU cores i 1.5GB RAM dla lepszej wydajności przy obsłudze równoległych wywołań LLM. Frontend w development jest ograniczony do 0.5 CPU i 256MB, co wystarcza dla hot reload, natomiast w produkcji (Nginx) potrzebuje 1 CPU i 512MB.

PostgreSQL z pgvector alokuje 1 CPU i 1GB RAM w development, ale w produkcji skaluje się do 2 CPU i 4GB dla obsługi embeddings i wektorowych zapytań. Redis, będący in-memory database, otrzymuje 256MB w dev i 1GB w prod. Neo4j, najbardziej resource-hungry serwis, wymaga 2GB w development i aż 8GB w produkcji dla przetwarzania złożonych grafów i Graph Data Science algorithms.

## Local Development

### Quick Start

Uruchomienie pełnego środowiska deweloperskiego wymaga jedynie Docker Compose. Komenda `docker-compose up -d` startuje wszystkie pięć serwisów w trybie detached. Po pierwszym uruchomieniu konieczne jest wykonanie migracji bazy danych przez `docker-compose exec api alembic upgrade head` oraz inicjalizacja indeksów Neo4j przez `python scripts/init_neo4j_indexes.py`. Ten drugi krok jest krytyczny - bez indeksów wektorowych system RAG nie będzie funkcjonował poprawnie.

Aplikacja po starcie jest dostępna pod kilkoma endpointami. Backend API odpowiada na `http://localhost:8000`, z interaktywną dokumentacją Swagger UI pod `/docs`. Frontend dev server działa na `http://localhost:5173` z hot reload. Neo4j Browser, użyteczny do debugowania grafów, znajduje się pod `http://localhost:7474`. PostgreSQL nasłuchuje na porcie 5433 (nie standardowy 5432, aby uniknąć konfliktów z lokalnymi instalacjami), a Redis na standardowym 6379.

### Hot Reload i Rebuilds

System jest zoptymalizowany dla developer experience. Zmiany w kodzie Python (backend) lub TypeScript/React (frontend) są natychmiast widoczne dzięki volume mounts i hot reload - nie wymaga to rebuildu kontenerów. Jedynie zmiany w `requirements.txt` lub `package.json` wymagają przebudowania odpowiedniego serwisu przez `docker-compose up --build -d api` lub `docker-compose up --build -d frontend`.

Migracje bazy danych po zmianach w modelach ORM można wygenerować automatycznie przez `docker-compose exec api alembic revision --autogenerate -m "opis zmiany"`, a następnie zastosować przez `alembic upgrade head`. System wykrywa zmiany w SQLAlchemy models i generuje odpowiednie DDL SQL.

### Debugging

Gdy coś nie działa, kluczowe są logi. Komenda `docker-compose logs -f api` streamuje logi backendu w real-time, co pozwala śledzić requesty HTTP, błędy Python, oraz wywołania LLM. Dla frontendu analogicznie `docker-compose logs -f frontend` pokazuje output Vite dev server.

W przypadku poważniejszych problemów można wejść do wnętrza kontenera przez `docker exec -it <container_name> bash`. Pozwala to na inspekcję plików, uruchomienie shell Python, czy sprawdzenie zmiennych środowiskowych. Komenda `docker stats` wyświetla real-time użycie CPU, RAM i network dla wszystkich kontenerów - przydatne przy debugowaniu performance issues.

## Cloud Run Production

### Architektura Single Service

W przeciwieństwie do tradycyjnego podejścia z osobnymi serwisami dla frontendu i backendu, Sight deployuje się jako jedna usługa Cloud Run. Dockerfile.cloudrun wykorzystuje multi-stage build: najpierw buduje frontend React z Vite (generując statyczne pliki w `/dist`), następnie instaluje Python dependencies dla backendu, a finalny stage łączy oba - FastAPI serwuje zarówno API endpoints (`/api/v1/*`) jak i statyczne pliki frontendu (`/`, `/assets/*`).

To rozwiązanie ma kilka zalet. Po pierwsze, prostota - jedna usługa Cloud Run zamiast dwóch oznacza mniej konfiguracji, mniej secrets do zarządzania, i niższe koszty (jedna instancja zamiast dwóch). Po drugie, brak CORS issues - frontend i backend są pod tym samym origin. Po trzecie, łatwiejsze routing - Cloud Run Load Balancer kieruje cały traffic do jednego serwisu.

### Google Cloud Platform Setup

Deployment wymaga najpierw skonfigurowania GCP. Projekt `gen-lang-client-0508446677` ma włączone pięć kluczowych API: Cloud Run (uruchamianie kontenerów), Cloud Build (CI/CD pipeline), Artifact Registry (storage dla Docker images), Secret Manager (bezpieczne przechowywanie credentials), oraz Cloud SQL Admin (zarządzanie bazą PostgreSQL).

Cloud SQL instancja `sight` została utworzona w regionie `europe-central2` (Warsaw) na tier `db-f1-micro` (0.6GB RAM, shared CPU) z 10GB SSD storage. To wystarczające dla małych i średnich obciążeń - instancja kosztuje około 10-15 USD miesięcznie. Backup automatyczny wykonuje się codziennie o 3:00 AM, z retencją 7 dni. Maintenance window ustawiony jest na niedziele o 4:00 AM, minimalizując wpływ na użytkowników.

### External Services

Oprócz Cloud SQL, aplikacja integruje się z dwoma managed services zewnętrznymi. Neo4j AuraDB Free tier (50,000 nodes, 0 USD/miesiąc) hostuje graf dla systemu RAG. Instancja znajduje się w regionie `europe-west1` (Belgium), co daje latencję ~20ms z Cloud Run w Warsaw. Connection string ma format `neo4j+s://xxxxx.databases.neo4j.io` - protokół `neo4j+s` jest wymagany dla AuraDB (nie `bolt://` jak w lokalnym Neo4j).

Upstash Redis w Free tier (10,000 requests/day) pełni rolę cache'a dla segment briefs i KPI snapshots. Region również `europe-west1`. Connection string: `redis://default:PASSWORD@region.upstash.io:PORT`. Upstash automatycznie evictuje najmniej używane keys gdy limit jest bliski przekroczenia.

### Secrets Management

Wszystkie wrażliwe dane (API keys, passwords, connection strings) są przechowywane w GCP Secret Manager, nie w zmiennych środowiskowych czy plikach .env. Mamy siedem secrets:

- `GOOGLE_API_KEY` - Gemini API key dla LLM operations
- `NEO4J_URI` i `NEO4J_PASSWORD` - credentials do AuraDB
- `REDIS_URL` - pełny connection string do Upstash
- `DATABASE_URL_CLOUD` - PostgreSQL connection string przez Unix socket (`/cloudsql/...`)
- `POSTGRES_PASSWORD` - hasło użytkownika postgres
- `SECRET_KEY` - FastAPI session signing key (32-char random hex)

Secrets są automatycznie montowane do Cloud Run przez parametr `--set-secrets` w deploy command. Cloud Run service account ma rolę `roles/secretmanager.secretAccessor` dla każdego secretu. Wartości są dostępne w kontenerze jako zmienne środowiskowe, ale nigdy nie są wyświetlane w logach czy Cloud Console UI.

Skrypt `scripts/setup-gcp-secrets.sh` automatyzuje tworzenie i aktualizację wszystkich secrets. Generuje `SECRET_KEY` przez `openssl rand -hex 32`, buduje `DATABASE_URL_CLOUD` z `POSTGRES_PASSWORD`, oraz nadaje uprawnienia service account. To znacznie przyspiesza setup nowych środowisk.

## CI/CD Pipeline

### Overview

Pełny deployment pipeline jest zdefiniowany w `cloudbuild.yaml` i składa się z siedmiu sekwencyjnych kroków: quality checks, unit tests, Docker build, database migrations, Cloud Run deploy, Neo4j initialization, oraz smoke tests. Pipeline uruchamia się automatycznie przy każdym push do branch `cleanup/dead-code-removal` przez Cloud Build trigger podpięty do GitHub repo `JakWdo/Symulacja`.

Całkowity czas wykonania wynosi **5-8 minut** dla incremental builds (z cache'owaniem Docker layers), lub **20-25 minut** dla first build bez cache. Code-only changes (bez zmian w dependencies) kompletują w **3-5 minut** dzięki aggressive layer caching. Pipeline używa explicit `--cache-from` dla maximum cache hit rate.

### Step 1: Code Quality (parallel)

Pierwsze trzy kroki wykonują się równolegle (każdy z `waitFor: ['-']`), oszczędzając 2-3 minuty. **Linting** używa ruff, szybkiego Python lintera, który sprawdza kod pod kątem błędów składniowych (E, F), stylu (W), sortowania importów (I), naming conventions (N), oraz modernizacji do Python 3.11+ (UP). Ruff jest 10-100x szybszy od flake8 i kompletuje w ~30 sekund.

**Type checking** z mypy weryfikuje type hints. Jednak ze względu na ekosystem Python (wiele bibliotek bez stubs) używamy lenient settings: `--ignore-missing-imports`, `--no-strict-optional`. Mypy warnings nie blokują buildu - są traktowane jako informacyjne. W przyszłości planujemy strict type checking po dodaniu stubs dla głównych dependencies.

**Security scan** wykorzystuje bandit do wykrywania common security issues: SQL injection, command injection, hardcoded passwords, insecure deserialization. Bandit również nie blokuje buildu (dużo false positives), ale warnings są reviewowane manualnie.

### Step 2: Unit Tests (blocking)

Po zakończeniu quality checks startuje krok testów jednostkowych. Wykonuje się ~240 testów oznaczonych jako **nie** integration/e2e/slow/external/manual/performance. Te testy są w pełni izolowane - nie wymagają PostgreSQL, Neo4j ani Redis. Wszystkie external dependencies są mockowane przez pytest-mock.

Testy uruchamiają się z coverage reporting (`--cov=app`). Threshold wynosi 80% - build failuje jeśli coverage spadnie poniżej. Obecnie utrzymujemy ~85% coverage dla services i ~92% dla models. Timeout dla całego test suite to 300 sekund - testy które nie kończą się w 5 minut są killed.

Jeśli choć jeden test failuje, cały build się przerywa z exit code 1. Jest to **blocking step** - deployment nie następuje jeśli unit tests nie przechodzą. Dzięki temu eliminujemy regression bugs przed wdrożeniem do produkcji.

### Step 3-4: Build & Push

Po pomyślnych testach następuje build Docker image z `Dockerfile.cloudrun`. Multi-stage build zajmuje **3-5 minut** dla code-only changes lub **15-20 minut** dla zmian w dependencies, dzięki Docker layer caching z explicit `--cache-from`. Image jest tagowany dwoma tagami: `latest` (zawsze wskazuje na najnowszy build) oraz `$COMMIT_SHA` (konkretny git commit dla rollback).

Push do Artifact Registry w `europe-central2-docker.pkg.dev` następuje natychmiast po build. Registry automatycznie skanuje image pod kątem CVEs i wyświetla wyniki w Cloud Console. Critical CVEs powinny być naprawione przed deploy do produkcji.

### Step 5: Database Migrations (critical)

**Najważniejszy krok całego pipeline.** Przed wdrożeniem nowego kodu aplikacji, schema bazy danych musi być up-to-date. Cloud Run Job `db-migrate` uruchamia komendę `alembic upgrade head` wewnątrz tego samego Docker image który będzie deployowany.

Job ma dostęp do Cloud SQL przez Unix socket (`--add-cloudsql-instances`) i używa `DATABASE_URL_CLOUD` secret. Jeśli migracja failuje (np. syntax error w migration script, constraint violation), build się przerywa. To zapobiega deployment broken code który nie może się połączyć z bazą.

Migracje są wykonywane jako Cloud Run Job (nie exec w działającym kontenerze) z dwóch powodów. Po pierwsze, isolation - job działa w czystym environment z maksymalnie 300s timeout. Po drugie, retry logic - job automatycznie retry-uje do 2 razy przy transient failures (network blips, Cloud SQL restarts).

### Step 6: Cloud Run Deploy

Deployment do Cloud Run używa `gcloud run deploy` z parametrami zoptymalizowanymi dla FastAPI + LLM workload:

- `--memory=2Gi` - wystarczające dla FastAPI + Redis client + Neo4j driver w memory
- `--cpu=2` - dwa vCPU pozwalają na parallel processing LLM requests
- `--cpu-boost` - temporary CPU boost podczas startu kontenera (cold start optimization)
- `--timeout=300` - 5 minut timeout dla długich LLM operations (focus groups)
- `--min-instances=0` - scale to zero gdy brak traffic (cost optimization)
- `--max-instances=5` - auto-scale do 5 instancji przy heavy load
- `--execution-environment=gen2` - nowszy runtime z lepszą performance

Secrets są montowane jako environment variables (`--set-secrets=DATABASE_URL=DATABASE_URL_CLOUD:latest,...`). Cloud Run automatycznie pobiera najnowsze wersje secrets - nie trzeba manualnie aktualizować deployment po zmianie secretu.

Deployment zajmuje 1-2 minuty. Cloud Run czeka aż nowa rewizja przejdzie health check (`/health` endpoint musi zwrócić 200 OK przez 10 sekund), dopiero wtedy kieruje traffic. Jeśli health check failuje przez 4 minuty, deployment jest rollbackowany automatycznie.

### Step 7: Neo4j Initialization (non-blocking)

Po deployment aplikacji, osobny Cloud Run Job `neo4j-init` uruchamia `python scripts/init_neo4j_cloudrun.py`. Skrypt tworzy trzy kluczowe indeksy w Neo4j:

- `document_id_idx` - B-tree index na `Document.id` dla szybkich lookupów
- `chunk_embedding_idx` - property index na `Chunk.embedding` (metadata)
- `chunk_vector_idx` - **vector index** na `Chunk.embedding` z 3072 wymiarami (Gemini embeddings), cosine similarity

Vector index jest wymagany dla hybrid search RAG. Bez niego queries `db.index.vector.queryNodes()` failują z `VectorIndexNotFoundError`. Tworzenie indeksu zajmuje 30-60 sekund dla typowej bazy z ~10,000 chunks.

Ten krok jest **non-blocking** - jeśli failuje (np. Neo4j timeout, network issues), build się nie przerywa. Aplikacja działa normalnie, ale RAG features są limited dopóki indeksy nie zostaną utworzone. Background task w FastAPI retry-uje połączenie z Neo4j co 5 minut.

### Step 8: Smoke Tests (verification)

Ostatni krok wykonuje cztery smoke tests na fresh deployowanej aplikacji:

1. **Health check** - `GET /health` musi zwrócić 200 OK z JSON payload `{"status": "healthy"}`
2. **Startup probe** - `GET /startup` weryfikuje połączenia do PostgreSQL, Redis, Neo4j
3. **API docs** - `GET /docs` sprawdza czy Swagger UI jest dostępne
4. **Frontend** - `GET /` zwraca React SPA (nie 404)

Jeśli którykolwiek test failuje, build jest oznaczony jako failed. To **blocking step** - informuje zespół że deployment się nie powiódł mimo że Cloud Run deploy sukceeded. W przyszłości planujemy automatic rollback do poprzedniej rewizji przy failed smoke tests.

### Monitoring Builds

Logi z każdego build są dostępne w Cloud Console lub przez CLI: `gcloud builds list --limit=5` pokazuje ostatnie buildy z statusem (SUCCESS/FAILURE/TIMEOUT). Dla szczegółów konkretnego build: `gcloud builds log <BUILD_ID> --stream` streamuje logi w real-time.

Każdy krok pipeline ma assigned ID (np. `lint`, `unit-tests`, `deploy`). Można sprawdzić status konkretnego kroku przez `gcloud builds describe <BUILD_ID> --format="json" | jq '.steps[] | {id, status, timing}'`. To pokazuje który krok failował i ile czasu zajął.

## Monitoring i Troubleshooting

### Cloud Logging

Wszystkie logi z Cloud Run są automatycznie przekazywane do Cloud Logging. Query language pozwala na precyzyjne filtrowanie. Przykład: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight AND severity>=ERROR" --limit=50` pokazuje tylko błędy z ostatnich 50 wpisów.

Logi zawierają structured fields: timestamp, severity (DEBUG/INFO/WARNING/ERROR/CRITICAL), textPayload (message), httpRequest (dla HTTP logs), oraz labels (custom metadata). FastAPI automatycznie loguje każdy request z method, path, status code i latency.

### Common Issues

**Problem 1: Service timeout podczas startu** - symptom: Cloud Run deployment sukceeded ale /health zwraca 504 Gateway Timeout. Przyczyna: aplikacja startuje >4 minuty (Cloud Run limit). Rozwiązanie: zwiększyć `--timeout` lub zoptymalizować startup (lazy initialization zamiast eager).

**Problem 2: Database connection failed** - symptom: logi pokazują `OperationalError: could not connect to server`. Przyczyna: źle skonfigurowany `DATABASE_URL_CLOUD` secret lub brak uprawnienia do Cloud SQL. Rozwiązanie: zweryfikować format connection string (`postgresql+asyncpg://...?host=/cloudsql/...`) i sprawdzić czy service account ma rolę `roles/cloudsql.client`.

**Problem 3: Neo4j timeout** - symptom: `/startup` endpoint pokazuje `"neo4j": "connection_failed"`. Przyczyna: Neo4j AuraDB wymaga `neo4j+s://` URI (nie `bolt://`), lub firewall blokuje Cloud Run IP. Rozwiązanie: zaktualizować `NEO4J_URI` secret i dodać `0.0.0.0/0` do allowlist w AuraDB Console (Cloud Run ma dynamiczne IPs).

**Problem 4: Frontend 404** - symptom: `GET /` zwraca 404 Not Found, API działa. Przyczyna: statyczne pliki frontendu nie zostały skopiowane do Docker image (błąd w Dockerfile.cloudrun). Rozwiązanie: zweryfikować `COPY --from=frontend-builder /app/dist /app/static` w Dockerfile i sprawdzić czy `app.mount("/", StaticFiles(directory="static", html=True))` jest w main.py.

**Problem 5: Slow LLM responses** - symptom: timeout errors przy generowaniu person lub focus groups. Przyczyna: niewystarczające CPU/RAM lub Gemini API throttling. Rozwiązanie: zwiększyć `--cpu=4 --memory=4Gi` lub zaimplementować rate limiting + request queuing.

### Performance Metrics

Target metrics dla produkcji:

- **API latency** - P95 < 500ms dla prostych endpoints, < 3s dla LLM-powered
- **Persona generation** - 20 person < 60s (obecnie ~45s dzięki parallel processing)
- **Focus group** - 20 person × 4 pytania < 3 minuty (obecnie ~2 min)
- **Cold start** - < 10s dla pierwszego request po scale-to-zero (dzięki `--cpu-boost`)
- **Memory usage** - < 1.5GB sustained (2GB limit daje buffer dla peaks)

Metrics są monitorowane przez Cloud Monitoring. Dashboard pokazuje request count, latency percentiles (P50/P90/P95/P99), error rate, CPU/memory utilization, oraz active instances count. Alerty są skonfigurowane dla error rate > 1% lub latency P95 > 5s.

## Koszty i Optymalizacja

### Monthly Cost Breakdown

Dla małego projektu (~100 users, 1000 requests/day) miesięczne koszty wynoszą około **16-30 USD**:

- Cloud Run (sight): $5-10 - zależne od request count i compute time
- Cloud SQL (db-f1-micro): $10-15 - stały koszt za instancję + storage
- Neo4j AuraDB Free: $0 - darmowy tier do 50k nodes
- Upstash Redis Free: $0 - darmowy tier do 10k requests/day
- Cloud Build: $0-2 - pierwsze 120 minut/dzień są free
- Artifact Registry: $1-3 - storage + egress

Największym kosztem jest Cloud SQL. Dla jeszcze niższych kosztów można rozważyć Cloud SQL Serverless (pay-per-use) lub migrację do managed PostgreSQL od innego providera (Supabase, Neon).

### Cost Optimization Tips

**Cloud Run auto-scaling** - dzięki `--min-instances=0` aplikacja scale-uje do zero instancji gdy brak traffic. Płacimy tylko za actual compute time, nie za idle instances. Dla ~1000 requests/day (średnio 500ms/request) to ~8 minut compute time dziennie = $0.20/dzień = $6/miesiąc.

**Gemini Flash zamiast Pro** - Flash model kosztuje $0.00005/1k input tokens (Pro: $0.00125 = 25x drożej). Dla większości operacji (generowanie person, focus group responses) Flash daje wystarczającą jakość. Pro używamy tylko dla complex analysis i summarization.

**Redis cache hits** - segment briefs są cache'owane w Redis na 7 dni. Cache hit rate ~80% oznacza 80% mniej wywołań Gemini API = oszczędność ~$15-20/miesiąc dla aktywnego użytkowania.

**Docker layer caching** - Cloud Build cache'uje Docker layers między buildami z explicit `--cache-from` source. Jeśli `requirements.txt` i `package.json` się nie zmieniły, instalacja dependencies jest skipped = build zajmuje 3-5 minut zamiast 20-25. Mniej compute time = niższe koszty Cloud Build (~$0.50-1.00 oszczędności per build).

---

**Ostatnia aktualizacja:** 2025-10-22
**Wersja:** 1.1
**Status:** Production-ready
