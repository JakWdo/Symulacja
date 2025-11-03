# Infrastruktura i Deployment - Sight Platform

**Ostatnia aktualizacja:** 2025-11-03
**Wersja:** 2.0
**Status:** Production-ready

---

## Spis Treści

1. [Przegląd Infrastruktury](#przegląd-infrastruktury)
2. [Architektura Docker](#architektura-docker)
3. [Local Development](#local-development)
4. [Cloud Run Production](#cloud-run-production)
5. [External Services](#external-services)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring & Observability](#monitoring--observability)

---

## Przegląd Infrastruktury

Platforma Sight została zaprojektowana z myślą o nowoczesnej architekturze kontenerowej, która zapewnia spójność między środowiskiem deweloperskim a produkcyjnym. System opiera się na pięciu kluczowych serwisach uruchamianych w kontenerach Docker: PostgreSQL z rozszerzeniem pgvector dla wektorowych operacji AI, Redis jako warstwa cache'owania i zarządzania sesjami, Neo4j z pluginami APOC i Graph Data Science dla zaawansowanych analiz grafowych, backend FastAPI z asynchronicznym przetwarzaniem oraz frontend React z TypeScript.

Nasza infrastruktura przeszła przez znaczące optymalizacje w ostatnich miesiącach. Udało się zmniejszyć rozmiar obrazów Docker o 84% (z 55GB do 11GB), zredukować czas budowania o 67%, oraz naprawić 54 CVE związanych z bezpieczeństwem. Deployment został w pełni zautomatyzowany - od push do GitHub do działającej aplikacji w Cloud Run zajmuje obecnie 8-12 minut, z automatycznymi migracjami bazy danych i inicjalizacją indeksów Neo4j.

### Kluczowe Cele Architektury

Infrastruktura Sight realizuje cztery nadrzędne cele. Pierwszym z nich jest **consistency across environments** - kod który działa lokalnie musi działać identycznie w produkcji. Dlatego używamy tych samych obrazów Docker, tych samych wersji dependencies i tej samej konfiguracji sieciowej zarówno na maszynach deweloperskich jak i w Cloud Run. Drugi cel to **developer experience** - deweloper powinien móc uruchomić pełny stack jedną komendą (`docker-compose up -d`) i natychmiast zacząć kodować z hot reload. Trzeci cel to **cost optimization** - Cloud Run scale-uje do zera instancji gdy nie ma ruchu, Redis cache redukuje wywołania LLM o 80%, a aggressive Docker layer caching oszczędza czas i pieniądze w CI/CD. Czwarty cel to **observability** - każda operacja jest logowana ze structured fields, metryki wydajnościowe są śledzone w real-time, a alerts informują zespół o anomaliach zanim wpłyną na użytkowników końcowych.

### Stack Technologiczny

**Backend Infrastructure:**
- FastAPI 0.110+ (async Python web framework)
- SQLAlchemy 2.0 (async ORM z connection pooling)
- PostgreSQL 15 z pgvector (wektorowa baza danych)
- Redis 7 (cache, rate limiting, distributed locking)
- Neo4j 5.x (grafowa baza wiedzy dla RAG)
- Uvicorn (ASGI server z multiple workers)

**Frontend Infrastructure:**
- React 18 + TypeScript (komponentowa architektura)
- Vite 5.x (ultra-fast dev server + build tool)
- TanStack Query (server state management z automatic caching)
- Zustand (lightweight UI state management)
- Nginx (static file serving w produkcji)

**Deployment Infrastructure:**
- Docker Compose (local development orchestration)
- Google Cloud Run (serverless container platform)
- Google Artifact Registry (Docker image storage)
- Google Cloud Build (CI/CD automation)
- Google Secret Manager (secure credentials storage)
- Google Cloud SQL (managed PostgreSQL w produkcji)

**External Services (Production):**
- Neo4j AuraDB Free (50,000 nodes, Europe West 1)
- Upstash Redis Free (10,000 requests/day, Europe West 1)
- Google Gemini API (LLM provider - Flash i Pro modele)

---

## Architektura Docker

### Multi-Stage Builds

Każdy serwis wykorzystuje wieloetapowe buildy Docker, które drastycznie redukują rozmiar finalnych obrazów. Backend FastAPI przechodzi przez trzy etapy: builder (instalacja dependencies z pip wheel compilation), runtime (kopiowanie aplikacji i config files), oraz production (minimalistyczny obraz z tylko niezbędnymi zależnościami). Frontend React również korzysta z czterech etapów: deps (node_modules installation), builder (Vite build do /dist), dev (serwer deweloperski z hot reload), oraz prod (statyczny Nginx serwujący zbudowane pliki).

**Dockerfile.cloudrun - Production Image:**

Produkcyjny Dockerfile łączy frontend i backend w jeden obraz, co upraszcza deployment i eliminuje CORS issues. Pierwszy stage builduje frontend React używając Vite - wszystkie statyczne assety trafiają do `/dist` folderu z hash suffixes dla cache busting. Drugi stage instaluje Python dependencies używając pip z wheel compilation dla native extensions (numpy, scipy dla embeddings). Trzeci stage kopiuje zbudowany frontend do `/app/static`, instaluje backend Python code, i konfiguruje uvicorn jako entry point. Finalny obraz waży około 2.8GB (poprzednio 5.5GB przed optymalizacjami), co przekłada się na szybsze deploymenty i niższe koszty network egress.

**Docker Compose - Local Development:**

Konfiguracja `docker-compose.yml` definiuje siedem serwisów (postgres, redis, neo4j, migrate, neo4j-init, api, frontend) z precyzyjnie skonfigurowanymi health checks i dependency chains. Health checks zapewniają że serwisy startują w poprawnej kolejności - PostgreSQL musi być healthy zanim migrate uruchomi alembic, a Neo4j musi być healthy zanim neo4j-init utworzy indeksy. Wszystkie serwisy są połączone do jednej sieci `backend` dla internal communication, co pozwala im komunikować się po nazwach hostów (np. `postgres:5432`, `redis:6379`) zamiast IP addresses.

### Resource Limits

Każdy serwis ma zdefiniowane limity CPU i RAM zarówno dla środowiska deweloperskiego jak i produkcyjnego. Backend API w development wykorzystuje 1 CPU core i 512MB RAM, podczas gdy w produkcji otrzymuje 2 CPU cores i 1.5GB RAM dla lepszej wydajności przy obsłudze równoległych wywołań LLM. Frontend w development jest ograniczony do 0.5 CPU i 256MB, co wystarcza dla hot reload, natomiast w produkcji (Nginx) potrzebuje 1 CPU i 512MB.

PostgreSQL z pgvector alokuje 1 CPU i 1GB RAM w development, ale w produkcji skaluje się do 2 CPU i 4GB dla obsługi embeddings i wektorowych zapytań. Redis, będący in-memory database, otrzymuje 256MB w dev i 1GB w prod. Neo4j, najbardziej resource-hungry serwis, wymaga 2GB w development i aż 8GB w produkcji dla przetwarzania złożonych grafów i Graph Data Science algorithms.

**docker-compose.yml - Resource Configuration:**

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 1G

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  neo4j:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 3G
        reservations:
          cpus: '0.5'
          memory: 1G
```

Reservations określają minimalny guaranteed resource allocation, podczas gdy limits definiują maksymalny burst capacity. To pozwala na elastyczne zarządzanie resources - serwisy mogą burst powyżej reservations gdy host ma wolne zasoby, ale nigdy nie przekroczą limits.

### Volume Management

Docker volumes zapewniają persistence dla danych między restartami kontenerów. Mamy pięć named volumes: `postgres_data` dla bazy danych, `redis_data` dla Redis persistence (AOF enabled), `neo4j_data` i `neo4j_logs` dla Neo4j, oraz `frontend_node_modules` aby uniknąć reinstalacji node_modules przy każdym rebuild kontenera frontend.

Named volumes są zarządzane przez Docker daemon i przetrwają `docker-compose down`. Aby całkowicie wyczyścić środowisko (fresh start), trzeba użyć `docker-compose down -v` który usuwa volumes, lub manualnie `docker volume rm sight_postgres_data`. Bind mounts (`./:/app` dla hot reload) montują lokalne foldery bezpośrednio do kontenera, co pozwala na natychmiastowe odbicie zmian w kodzie bez rebuildu.

### Networking

Wszystkie serwisy są połączone do custom network `backend` (bridge driver). To zapewnia izolację od innych Docker containers na hoście oraz pozwala na automatic DNS resolution - każdy serwis jest dostępny po nazwie (np. `postgres`, `redis`, `neo4j`) z automatycznym load balancing jeśli skalujemy replicas. Port publishing (`ports: - "8000:8000"`) eksponuje serwisy na hoście dla dostępu z lokalnej maszyny, ale internal communication używa Docker network bez port mappings.

---

## Local Development

### Quick Start

Uruchomienie pełnego środowiska deweloperskiego wymaga jedynie Docker Compose. Pierwsze co trzeba zrobić to skonfigurować zmienne środowiskowe. Kopiujemy `.env.example` do `.env` i wypełniamy wymagane wartości: `GOOGLE_API_KEY` (Gemini API key z Google AI Studio), `SECRET_KEY` (32-char random hex wygenerowany przez `openssl rand -hex 32`), oraz credentials do PostgreSQL, Redis i Neo4j (defaults w docker-compose są OK dla developmentu, ale production wymaga silniejszych haseł).

**Komendy startowe:**

```bash
# 1. Konfiguracja środowiska
cp .env.example .env
# Edytuj .env - ustaw GOOGLE_API_KEY i SECRET_KEY

# 2. Uruchom wszystkie serwisy
docker-compose up -d

# 3. Sprawdź logi startup (opcjonalnie)
docker-compose logs -f

# 4. Weryfikuj że wszystko działa
curl http://localhost:8000/health
# {"status": "healthy", "postgres": "connected", "redis": "connected", "neo4j": "connected"}
```

Po pierwszym uruchomieniu migrate i neo4j-init service'y wykonają się automatycznie dzięki dependency chain w docker-compose. Migrate uruchamia `alembic upgrade head` aby zastosować wszystkie migracje bazy danych. Neo4j-init uruchamia `scripts/init_neo4j_indexes.py` który tworzy trzy kluczowe indeksy: `document_id_idx` (B-tree na Document.id), `chunk_embedding_idx` (property index na Chunk.embedding), oraz `chunk_vector_idx` (vector index z 768 wymiarami dla Gemini embeddings). Te indeksy są wymagane dla systemu RAG - bez nich hybrid search failuje z `VectorIndexNotFoundError`.

### Dostępne Endpointy

Aplikacja po starcie jest dostępna pod kilkoma endpointami. Backend API odpowiada na `http://localhost:8000`, z interaktywną dokumentacją Swagger UI pod `/docs` i ReDoc pod `/redoc`. Frontend dev server działa na `http://localhost:5173` z hot reload - każda zmiana w plikach `.tsx` lub `.ts` automatycznie rebuilds i refreshuje przeglądarkę. Neo4j Browser, użyteczny do debugowania grafów, znajduje się pod `http://localhost:7474` (credentials: neo4j/dev_password_change_in_prod). PostgreSQL nasłuchuje na porcie 5433 (nie standardowy 5432, aby uniknąć konfliktów z lokalnymi instalacjami), a Redis na standardowym 6379.

**Przydatne endpointy API:**

- `GET /health` - Health check all dependencies
- `GET /startup` - Detailed startup probe (z latencjami DB connections)
- `GET /docs` - Swagger UI (interactive API docs)
- `GET /metrics` - Prometheus metrics (opcjonalny, wymaga włączenia)
- `POST /api/v1/projects/{id}/personas/generate` - Generuj 20 person
- `POST /api/v1/focus-groups` - Utwórz grupę fokusową

### Hot Reload i Rebuilds

System jest zoptymalizowany dla developer experience. Zmiany w kodzie Python (backend) lub TypeScript/React (frontend) są natychmiast widoczne dzięki volume mounts i hot reload - nie wymaga to rebuildu kontenerów. Backend używa uvicorn z flagą `--reload` która śledzi zmiany w `app/` i automatycznie restartuje worker processes. Frontend używa Vite dev server z ultra-fast HMR (Hot Module Replacement) który preserves application state podczas reload.

Jedynie zmiany w `requirements.txt` lub `package.json` wymagają przebudowania odpowiedniego serwisu. Dla backendu: `docker-compose up --build -d api`, dla frontendu: `docker-compose up --build -d frontend`. Rebuild zajmuje około 30-60 sekund dzięki Docker layer caching - tylko zmienione layers są rebuilowane, reszta jest reused z cache.

**Migracje bazy danych:**

Po zmianach w modelach ORM (`app/models/`) trzeba wygenerować i zastosować migrację Alembic. Proces jest półautomatyczny - Alembic wykrywa zmiany w SQLAlchemy models i generuje odpowiednie DDL SQL, ale należy zawsze przejrzeć wygenerowaną migrację przed zastosowaniem.

```bash
# 1. Auto-generuj migrację ze zmian w modelach
docker-compose exec api alembic revision --autogenerate -m "Add kpi_snapshot field to personas"

# 2. Przejrzyj wygenerowaną migrację
cat alembic/versions/XXXX_add_kpi_snapshot_field_to_personas.py

# 3. Zastosuj migrację
docker-compose exec api alembic upgrade head

# 4. Weryfikuj schema
docker-compose exec postgres psql -U sight -d sight_db -c "\d personas"
```

**WAŻNE:** Alembic może pominąć niektóre zmiany - szczególnie indeksy, custom SQL operations, data migrations. Zawsze reviewuj wygenerowaną migrację i dodaj brakujące operacje manualnie.

### Debugging

Gdy coś nie działa, kluczowe są logi. Komenda `docker-compose logs -f api` streamuje logi backendu w real-time, co pozwala śledzić requesty HTTP, błędy Python, oraz wywołania LLM. Dla frontendu analogicznie `docker-compose logs -f frontend` pokazuje output Vite dev server. Dla wszystkich serwisów jednocześnie: `docker-compose logs -f` (może być overwhelming).

**Filtrowanie logów:**

```bash
# Tylko błędy (ERROR level)
docker-compose logs api | grep ERROR

# Ostatnie 100 linii
docker-compose logs --tail=100 api

# Konkretny timestamp range (wymaga jq)
docker-compose logs --timestamps api | grep "2025-11-03"

# Follow logs z konkretnego serwisu
docker-compose logs -f postgres redis neo4j
```

W przypadku poważniejszych problemów można wejść do wnętrza kontenera przez `docker exec -it sight_api bash`. Pozwala to na inspekcję plików, uruchomienie shell Python (`python -c "from app.core.config import get_settings; print(get_settings())"` - wait, to już nie działa, teraz używamy `from config import app`), czy sprawdzenie zmiennych środowiskowych (`env | grep DATABASE`). Komenda `docker stats` wyświetla real-time użycie CPU, RAM i network dla wszystkich kontenerów - przydatne przy debugowaniu performance issues.

**Typowe problemy local development:**

**Problem 1: Port already in use**
Symptom: `Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use`
Przyczyna: Inny proces (lokalna instalacja FastAPI, Jupyter notebook) używa portu 8000
Rozwiązanie: `lsof -ti:8000 | xargs kill -9` lub zmień port w docker-compose.yml

**Problem 2: PostgreSQL connection refused**
Symptom: `OperationalError: could not connect to server: Connection refused`
Przyczyna: Postgres container nie wystartował (failed health check) lub DATABASE_URL ma złe credentials
Rozwiązanie: `docker-compose logs postgres` sprawdź logi, weryfikuj DATABASE_URL w .env

**Problem 3: Neo4j timeout**
Symptom: `ServiceUnavailable: Failed to establish connection`
Przyczyna: Neo4j jest wolny do startu (2-3 minuty przy pierwszym uruchomieniu)
Rozwiązanie: Poczekaj 2-3 minuty, sprawdź `docker-compose logs neo4j` czy wystartował

**Problem 4: Frontend hot reload nie działa**
Symptom: Zmiany w .tsx nie są widoczne w przeglądarce
Przyczyna: Volume mount nie działa (Windows WSL2 issue) lub Vite cache corruption
Rozwiązanie: `docker-compose restart frontend` lub `docker-compose exec frontend rm -rf node_modules/.vite`

**Problem 5: Out of memory**
Symptom: Containers crashują z exit code 137 (OOM killed)
Przyczyna: Docker Desktop ma za mało RAM alokowanego (default 2GB)
Rozwiązanie: Docker Desktop → Settings → Resources → Memory: zwiększ do minimum 8GB

### Database Management

**PostgreSQL:**

```bash
# Connect do bazy
docker-compose exec postgres psql -U sight -d sight_db

# Sprawdź tabele
\dt

# Sprawdź schema konkretnej tabeli
\d personas

# Wykonaj query
SELECT COUNT(*) FROM personas WHERE is_active = true;

# Export danych do CSV
\copy (SELECT * FROM personas) TO '/tmp/personas.csv' CSV HEADER

# Backup całej bazy
docker-compose exec postgres pg_dump -U sight sight_db > backup_$(date +%Y%m%d).sql

# Restore z backupu
cat backup_20251103.sql | docker-compose exec -T postgres psql -U sight -d sight_db
```

**Redis:**

```bash
# Connect do Redis
docker-compose exec redis redis-cli

# Sprawdź wszystkie keys (DEV ONLY - nie używaj w produkcji!)
KEYS *

# Sprawdź konkretny key
GET segment_brief:25-34:wyższe:warszawa:kobieta

# Sprawdź TTL (time to live)
TTL segment_brief:25-34:wyższe:warszawa:kobieta

# Flush cache (DEV ONLY)
FLUSHALL

# Sprawdź memory usage
INFO memory
```

**Neo4j:**

Otwórz Neo4j Browser w przeglądarce: `http://localhost:7474`
Credentials: `neo4j / dev_password_change_in_prod`

```cypher
// Sprawdź ile jest dokumentów RAG
MATCH (d:Document) RETURN count(d)

// Sprawdź ile jest chunków
MATCH (c:RAGChunk) RETURN count(c)

// Sprawdź graph nodes (Wskaźnik, Obserwacja, Trend, Demografia)
MATCH (n) WHERE n:Wskaznik OR n:Obserwacja OR n:Trend OR n:Demografia
RETURN labels(n) as type, count(n) as count

// Sprawdź przykładowy graph node
MATCH (w:Wskaznik) RETURN w LIMIT 5

// Sprawdź vector index
CALL db.indexes()

// Test vector search
CALL db.index.vector.queryNodes('chunk_vector_idx', 10, [0.1, 0.2, ...])
```

---

## Cloud Run Production

### Architektura Single Service

W przeciwieństwie do tradycyjnego podejścia z osobnymi serwisami dla frontendu i backendu, Sight deployuje się jako jedna usługa Cloud Run. Dockerfile.cloudrun wykorzystuje multi-stage build: najpierw buduje frontend React z Vite (generując statyczne pliki w `/dist`), następnie instaluje Python dependencies dla backendu, a finalny stage łączy oba - FastAPI serwuje zarówno API endpoints (`/api/v1/*`) jak i statyczne pliki frontendu (`/`, `/assets/*`).

To rozwiązanie ma kilka zalet. Po pierwsze, **prostota** - jedna usługa Cloud Run zamiast dwóch oznacza mniej konfiguracji, mniej secrets do zarządzania, i niższe koszty (jedna instancja zamiast dwóch). Po drugie, **brak CORS issues** - frontend i backend są pod tym samym origin, więc nie ma potrzeby konfiguracji CORS headers ani preflight OPTIONS requests. Po trzecie, **łatwiejsze routing** - Cloud Run Load Balancer kieruje cały traffic do jednego serwisu, a FastAPI internal router dystrybuuje requesty do API vs static files.

**app/main.py - Static Files Mounting:**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# API routes
app.include_router(api_router, prefix="/api/v1")

# Static files (frontend build) - MUST be after API routes
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

Kolejność jest krytyczna - API routes muszą być zarejestrowane PRZED static files mount, inaczej wszystkie requesty trafiłyby do static files handler i API nie działałoby. StaticFiles z `html=True` automatycznie serwuje `index.html` dla wszystkich ścieżek które nie pasują do API routes, co zapewnia poprawne działanie React Router (client-side routing).

### Google Cloud Platform Setup

Deployment wymaga najpierw skonfigurowania GCP. Projekt `gen-lang-client-0508446677` ma włączone pięć kluczowych API: Cloud Run (uruchamianie kontenerów), Cloud Build (CI/CD pipeline), Artifact Registry (storage dla Docker images), Secret Manager (bezpieczne przechowywanie credentials), oraz Cloud SQL Admin (zarządzanie bazą PostgreSQL).

**Włączanie API (jednorazowe):**

```bash
# Zaloguj się do GCP
gcloud auth login

# Ustaw projekt
gcloud config set project gen-lang-client-0508446677

# Włącz wymagane API
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

Cloud SQL instancja `sight` została utworzona w regionie `europe-central2` (Warsaw) na tier `db-f1-micro` (0.6GB RAM, shared CPU) z 10GB SSD storage. To wystarczające dla małych i średnich obciążeń - instancja kosztuje około 10-15 USD miesięcznie. Backup automatyczny wykonuje się codziennie o 3:00 AM, z retencją 7 dni. Maintenance window ustawiony jest na niedziele o 4:00 AM, minimalizując wpływ na użytkowników.

**Tworzenie Cloud SQL instancji (jednorazowe):**

```bash
# Utwórz Cloud SQL instancję
gcloud sql instances create sight \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=europe-central2 \
    --storage-type=SSD \
    --storage-size=10GB \
    --backup-start-time=03:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=4

# Utwórz bazę danych
gcloud sql databases create sight_db --instance=sight

# Utwórz użytkownika
gcloud sql users create sight --instance=sight --password=STRONG_PASSWORD_HERE

# Sprawdź connection name (potrzebny dla DATABASE_URL_CLOUD)
gcloud sql instances describe sight --format="value(connectionName)"
# Output: gen-lang-client-0508446677:europe-central2:sight
```

**Artifact Registry:**

```bash
# Utwórz repository dla Docker images
gcloud artifacts repositories create sight-containers \
    --repository-format=docker \
    --location=europe-central2 \
    --description="Docker images for Sight platform"

# Skonfiguruj Docker authentication
gcloud auth configure-docker europe-central2-docker.pkg.dev
```

---

## External Services

### Neo4j AuraDB

Oprócz Cloud SQL, aplikacja integruje się z dwoma managed services zewnętrznymi. Neo4j AuraDB Free tier (50,000 nodes, 0 USD/miesiąc) hostuje graf dla systemu RAG. Instancja znajduje się w regionie `europe-west1` (Belgium), co daje latencję około 20ms z Cloud Run w Warsaw. Connection string ma format `neo4j+s://xxxxx.databases.neo4j.io` - protokół `neo4j+s` jest wymagany dla AuraDB (nie `bolt://` jak w lokalnym Neo4j).

**Setup AuraDB (jednorazowe):**

1. Zarejestruj się na https://neo4j.com/cloud/aura/
2. Utwórz instancję Free tier w regionie Europe West 1
3. Zapisz connection URI i hasło (pokazane tylko raz!)
4. Skonfiguruj IP allowlist - dodaj `0.0.0.0/0` dla Cloud Run (dynamic IPs)
5. Dodaj credentials do Secret Manager (NEO4J_URI, NEO4J_PASSWORD)

**Ważne:** AuraDB używa `neo4j+s://` (secure WebSocket) zamiast `bolt://` (binary protocol). Aplikacja automatycznie detektuje protokół i używa odpowiedniego drivera.

### Upstash Redis

Upstash Redis w Free tier (10,000 requests/day) pełni rolę cache'a dla segment briefs i KPI snapshots. Region również `europe-west1` dla niskiej latencji. Connection string: `redis://default:PASSWORD@region.upstash.io:PORT`. Upstash automatycznie evictuje najmniej używane keys gdy limit jest bliski przekroczenia (LRU eviction policy).

**Setup Upstash (jednorazowe):**

1. Zarejestruj się na https://upstash.com/
2. Utwórz Redis database w regionie Europe West 1
3. Wybierz Free tier (10k requests/day, 256MB storage)
4. Skopiuj REST URL i konwertuj na Redis URL format
5. Dodaj REDIS_URL do Secret Manager

**Cache strategy:**

- Segment briefs: TTL 7 dni (604800s)
- Graph RAG context: TTL 7 dni
- KPI snapshots: TTL 5 minut (300s)
- Expected hit rate: 70-90% dla segment briefs, 80-95% dla graph context

### Secrets Management

Wszystkie wrażliwe dane (API keys, passwords, connection strings) są przechowywane w GCP Secret Manager, nie w zmiennych środowiskowych czy plikach .env. Mamy siedem secrets:

- `GOOGLE_API_KEY` - Gemini API key dla LLM operations
- `NEO4J_URI` i `NEO4J_PASSWORD` - credentials do AuraDB
- `REDIS_URL` - pełny connection string do Upstash
- `DATABASE_URL_CLOUD` - PostgreSQL connection string przez Unix socket
- `POSTGRES_PASSWORD` - hasło użytkownika postgres
- `SECRET_KEY` - FastAPI session signing key (32-char random hex)

**Tworzenie secrets (jednorazowe):**

```bash
# 1. Wygeneruj SECRET_KEY
openssl rand -hex 32

# 2. Utwórz secrets
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create GOOGLE_API_KEY --data-file=-
echo -n "neo4j+s://xxxxx.databases.neo4j.io" | gcloud secrets create NEO4J_URI --data-file=-
echo -n "YOUR_NEO4J_PASSWORD" | gcloud secrets create NEO4J_PASSWORD --data-file=-
echo -n "redis://default:PASSWORD@region.upstash.io:PORT" | gcloud secrets create REDIS_URL --data-file=-
echo -n "STRONG_POSTGRES_PASSWORD" | gcloud secrets create POSTGRES_PASSWORD --data-file=-
echo -n "$(openssl rand -hex 32)" | gcloud secrets create SECRET_KEY --data-file=-

# 3. Zbuduj DATABASE_URL_CLOUD (Unix socket dla Cloud SQL)
echo -n "postgresql+asyncpg://sight:POSTGRES_PASSWORD@/sight_db?host=/cloudsql/gen-lang-client-0508446677:europe-central2:sight" | gcloud secrets create DATABASE_URL_CLOUD --data-file=-

# 4. Nadaj uprawnienia Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe gen-lang-client-0508446677 --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in GOOGLE_API_KEY NEO4J_URI NEO4J_PASSWORD REDIS_URL DATABASE_URL_CLOUD POSTGRES_PASSWORD SECRET_KEY; do
    gcloud secrets add-iam-policy-binding $SECRET \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor"
done
```

Secrets są automatycznie montowane do Cloud Run przez parametr `--set-secrets` w deploy command. Cloud Run service account ma rolę `roles/secretmanager.secretAccessor` dla każdego secretu. Wartości są dostępne w kontenerze jako zmienne środowiskowe, ale nigdy nie są wyświetlane w logach czy Cloud Console UI.

**Aktualizacja secrets:**

```bash
# Utwórz nową wersję secretu
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# Cloud Run automatycznie użyje latest version przy następnym deploy
# Można też wymusić nową rewizję bez deploy:
gcloud run services update sight --region=europe-central2
```

---

## CI/CD Pipeline

### Overview

Pełny deployment pipeline jest zdefiniowany w `cloudbuild.yaml` i składa się z siedmiu sekwencyjnych kroków: pull cache, Docker build, push to registry, database migrations, Cloud Run deploy, Neo4j initialization, oraz smoke tests. Pipeline uruchamia się automatycznie przy każdym push do branch `main` przez Cloud Build trigger podpięty do GitHub repo `JakWdo/Symulacja`.

Całkowity czas wykonania wynosi **8-12 minut** dla incremental builds (z cache'owaniem Docker layers), lub **20-25 minut** dla first build bez cache. Code-only changes (bez zmian w dependencies) kompletują w **5-8 minut** dzięki aggressive layer caching. Pipeline używa explicit `--cache-from` oraz BuildKit inline cache dla maximum cache hit rate.

**Optimizations applied (October 2024):**

- BuildKit inline cache: zapisuje cache metadata wewnątrz image layers
- Pinned base images: `node:20.18.0`, `python:3.11.11` (prevents cache invalidation)
- Multi-stage caching: każdy stage (frontend-builder, backend-builder, runtime) jest cache'owany osobno
- Machine type E2_HIGHCPU_8: szybszy build (8 vCPU vs 1 vCPU default)
- Parallel quality checks: usunięte z cloudbuild.yaml (przenoszone do pre-commit hooks lokalnie)

### Step 1: Pull Cache

Pipeline zaczyna się od pobrania poprzedniego image z Artifact Registry aby użyć go jako cache source. Używamy `entrypoint: bash` z `|| true` aby uniknąć failowania na first build (no cache exists yet). Docker automatycznie użyje downloaded image jako cache source w następnym kroku.

```bash
docker pull europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest || echo "No cache image found - first build will be slow"
```

### Step 2: Build & Push

Build Docker image z `Dockerfile.cloudrun` używając BuildKit dla lepszego cachingu. Multi-stage build zajmuje 3-5 minut dla code-only changes lub 15-20 minut dla zmian w dependencies. Image jest tagowany dwoma tagami: `latest` (zawsze wskazuje na najnowszy build) oraz `$COMMIT_SHA` (konkretny git commit dla rollback).

```bash
export DOCKER_BUILDKIT=1

docker build \
  -f Dockerfile.cloudrun \
  --cache-from europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  -t europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:$COMMIT_SHA \
  .

docker push --all-tags europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight
```

Push do Artifact Registry następuje natychmiast po build. Registry automatycznie skanuje image pod kątem CVEs i wyświetla wyniki w Cloud Console. Critical CVEs powinny być naprawione przed deploy do produkcji.

### Step 3: Database Migrations (CRITICAL)

**Najważniejszy krok całego pipeline.** Przed wdrożeniem nowego kodu aplikacji, schema bazy danych musi być up-to-date. Cloud Run Job `db-migrate` uruchamia komendę `alembic upgrade head` wewnątrz tego samego Docker image który będzie deployowany.

Job ma dostęp do Cloud SQL przez Unix socket (`--add-cloudsql-instances`) i używa `DATABASE_URL_CLOUD` secret. Jeśli migracja failuje (np. syntax error w migration script, constraint violation), build się przerywa. To zapobiega deployment broken code który nie może się połączyć z bazą.

```bash
# Create or update migration job
gcloud run jobs create db-migrate \
  --image=europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  --region=europe-central2 \
  --add-cloudsql-instances=gen-lang-client-0508446677:europe-central2:sight \
  --set-secrets=DATABASE_URL=DATABASE_URL_CLOUD:latest \
  --command=alembic,upgrade,head \
  --max-retries=2 \
  --task-timeout=300

# Execute migrations
gcloud run jobs execute db-migrate --region=europe-central2 --wait

# Check exit code
if [ $? -eq 0 ]; then
  echo "✅ Migrations completed successfully"
else
  echo "❌ Migrations failed - aborting deployment"
  exit 1
fi
```

Migracje są wykonywane jako Cloud Run Job (nie exec w działającym kontenerze) z dwóch powodów. Po pierwsze, **isolation** - job działa w czystym environment z maksymalnie 300s timeout, bez ryzyka interference z running application. Po drugie, **retry logic** - job automatycznie retry-uje do 2 razy przy transient failures (network blips, Cloud SQL restarts).

### Step 4: Cloud Run Deploy

Deployment do Cloud Run używa `gcloud run deploy` z parametrami zoptymalizowanymi dla FastAPI + LLM workload:

```bash
gcloud run deploy sight \
  --image=europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  --region=europe-central2 \
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --memory=4Gi \
  --cpu=2 \
  --cpu-boost \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=5 \
  --execution-environment=gen2 \
  --add-cloudsql-instances=gen-lang-client-0508446677:europe-central2:sight \
  --set-secrets=DATABASE_URL=DATABASE_URL_CLOUD:latest,GOOGLE_API_KEY=GOOGLE_API_KEY:latest,NEO4J_PASSWORD=NEO4J_PASSWORD:latest,NEO4J_URI=NEO4J_URI:latest,POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,REDIS_URL=REDIS_URL:latest,SECRET_KEY=SECRET_KEY:latest \
  --set-env-vars=NEO4J_USER=neo4j,ENVIRONMENT=production,DEBUG=False,DEFAULT_LLM_PROVIDER=google,DEFAULT_MODEL=gemini-2.5-flash,EMBEDDING_MODEL=models/gemini-embedding-001,RAG_ENABLED=True,ORCHESTRATION_ENABLED=True
```

**Kluczowe parametry:**

- `--memory=4Gi` - wystarczające dla FastAPI + Redis client + Neo4j driver + sentence-transformers (~2.5GB peak)
- `--cpu=2` - dwa vCPU pozwalają na parallel processing LLM requests
- `--cpu-boost` - temporary CPU boost podczas startu kontenera (cold start optimization, reduces cold start z 10s → 5s)
- `--timeout=300` - 5 minut timeout dla długich LLM operations (focus groups z 20 person × 4 pytania ~2 min)
- `--min-instances=0` - scale to zero gdy brak traffic (cost optimization)
- `--max-instances=5` - auto-scale do 5 instancji przy heavy load (prevents runaway costs)
- `--execution-environment=gen2` - nowszy runtime z lepszą performance i security

Secrets są montowane jako environment variables (`--set-secrets=DATABASE_URL=DATABASE_URL_CLOUD:latest,...`). Cloud Run automatycznie pobiera najnowsze wersje secrets - nie trzeba manualnie aktualizować deployment po zmianie secretu.

Deployment zajmuje 1-2 minuty. Cloud Run czeka aż nowa rewizja przejdzie health check (`/health` endpoint musi zwrócić 200 OK przez 10 sekund), dopiero wtedy kieruje traffic. Jeśli health check failuje przez 4 minuty, deployment jest rollbackowany automatycznie do poprzedniej rewizji.

### Step 5: Neo4j Initialization

Po deployment aplikacji, osobny Cloud Run Job `neo4j-init` uruchamia `python scripts/init_neo4j_cloudrun.py`. Skrypt tworzy trzy kluczowe indeksy w Neo4j:

- `document_id_idx` - B-tree index na `Document.id` dla szybkich lookupów
- `chunk_embedding_idx` - property index na `Chunk.embedding` (metadata)
- `chunk_vector_idx` - **vector index** na `Chunk.embedding` z 768 wymiarami (Gemini embeddings), cosine similarity

Vector index jest wymagany dla hybrid search RAG. Bez niego queries `db.index.vector.queryNodes()` failują z `VectorIndexNotFoundError`. Tworzenie indeksu zajmuje 30-60 sekund dla typowej bazy z około 10,000 chunks.

```bash
# Create or update Neo4j init job
gcloud run jobs create neo4j-init \
  --image=europe-central2-docker.pkg.dev/gen-lang-client-0508446677/sight-containers/sight:latest \
  --region=europe-central2 \
  --set-secrets=NEO4J_URI=NEO4J_URI:latest,NEO4J_PASSWORD=NEO4J_PASSWORD:latest \
  --set-env-vars=NEO4J_USER=neo4j \
  --command=python,scripts/init_neo4j_cloudrun.py \
  --max-retries=3 \
  --task-timeout=300

# Execute initialization
gcloud run jobs execute neo4j-init --region=europe-central2 --wait

# Check status (non-fatal)
if [ $? -eq 0 ]; then
  echo "✅ Neo4j indexes initialized successfully"
else
  echo "⚠️ Neo4j init failed - RAG features may be limited"
fi
```

Ten krok jest **non-blocking** - jeśli failuje (np. Neo4j timeout, network issues), build się nie przerywa. Aplikacja działa normalnie, ale RAG features są limited dopóki indeksy nie zostaną utworzone. Background task w FastAPI retry-uje połączenie z Neo4j co 5 minut.

### Step 6: Smoke Tests

Ostatni krok wykonuje cztery smoke tests na fresh deployowanej aplikacji:

1. **Health check** - `GET /health` musi zwrócić 200 OK z JSON payload `{"status": "healthy"}`
2. **Startup probe** - `GET /startup` weryfikuje połączenia do PostgreSQL, Redis, Neo4j
3. **API docs** - `GET /docs` sprawdza czy Swagger UI jest dostępne
4. **Frontend** - `GET /` zwraca React SPA (nie 404)

```bash
# Get deployed service URL
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")

# Test 1: Health check
HEALTH_STATUS=$(curl -f -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health")
if [ "$HEALTH_STATUS" != "200" ]; then
  echo "❌ Health check FAILED"
  exit 1
fi

# Test 2: Frontend
FRONTEND_STATUS=$(curl -f -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/")
if [ "$FRONTEND_STATUS" != "200" ]; then
  echo "❌ Frontend FAILED"
  exit 1
fi

echo "🎉 Smoke tests PASSED!"
```

Jeśli którykolwiek test failuje, build jest oznaczony jako failed. To **blocking step** - informuje zespół że deployment się nie powiódł mimo że Cloud Run deploy sukceeded. W przyszłości planujemy automatic rollback do poprzedniej rewizji przy failed smoke tests.

### Monitoring Builds

Logi z każdego build są dostępne w Cloud Console lub przez CLI:

```bash
# Lista ostatnich buildów
gcloud builds list --limit=5

# Stream logs konkretnego build
gcloud builds log BUILD_ID --stream

# Szczegóły buildu (JSON)
gcloud builds describe BUILD_ID --format=json

# Status poszczególnych kroków
gcloud builds describe BUILD_ID --format="json" | jq '.steps[] | {id, status, timing}'
```

Każdy krok pipeline ma assigned ID (np. `pull-cache`, `build`, `deploy`). Można sprawdzić który krok failował i ile czasu zajął. To jest przydatne do debugowania slow builds czy identyfikacji bottlenecks w pipeline.

**Setup Cloud Build trigger (jednorazowe):**

```bash
# Utwórz trigger na push do main branch
gcloud builds triggers create github \
  --name="sight-deploy-main" \
  --repo-name="Symulacja" \
  --repo-owner="JakWdo" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml"
```

---

## Monitoring & Observability

### Cloud Logging

Wszystkie logi z Cloud Run są automatycznie przekazywane do Cloud Logging. Query language pozwala na precyzyjne filtrowanie.

**Przykłady queries:**

```bash
# Tylko błędy z ostatnich 50 wpisów
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight AND severity>=ERROR" --limit=50

# LLM operations z użyciem tokenów
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.operation=persona_generation" --limit=20 --format=json

# Slow queries (latency > 1s)
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.latency_ms>1000" --limit=20

# Requests z konkretnego user_id
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.user_id=USER_UUID" --limit=50
```

Logi zawierają structured fields: timestamp, severity (DEBUG/INFO/WARNING/ERROR/CRITICAL), textPayload (message), httpRequest (dla HTTP logs), oraz labels (custom metadata). FastAPI automatycznie loguje każdy request z method, path, status code i latency.

**Structured logging w aplikacji:**

```python
import logging

logger = logging.getLogger(__name__)

# Log LLM call z kontekstem
logger.info(
    "LLM generation completed",
    extra={
        "operation": "persona_generation",
        "model": "gemini-2.5-flash",
        "input_tokens": 1234,
        "output_tokens": 567,
        "latency_ms": 2800,
        "cost_usd": 0.00026,
        "user_id": str(user_id),
        "project_id": str(project_id)
    }
)
```

### Key Metrics to Track

**LLM Performance:**
- Tokens per operation (input/output)
- Cost per operation ($USD)
- Latency (p50, p90, p95, p99)
- Error rate (% failed calls)
- Retry rate (% calls requiring retry)

**RAG Performance:**
- Cache hit rate (hybrid search, graph RAG)
- Retrieval latency (vector, keyword, graph)
- Context size (chars, tokens)
- Relevance score (user feedback)

**Quality Metrics:**
- Persona quality score (0-100)
- Demographic accuracy (chi-square p-value)
- Consistency score (% personas passing checks)
- Hallucination rate (% outputs with facts not in RAG)

**Infrastructure Metrics:**
- API latency (p50, p90, p95, p99)
- Database query time (p95)
- Memory usage (MB, % of limit)
- CPU usage (%, throttling events)
- Active instances count
- Cold start frequency
- Error rate (HTTP 5xx)

### Cloud Monitoring Dashboard

Target metrics dla produkcji:

- **API latency** - P95 < 500ms dla prostych endpoints, < 3s dla LLM-powered
- **Persona generation** - 20 person < 60s (obecnie około 45s dzięki parallel processing)
- **Focus group** - 20 person × 4 pytania < 3 minuty (obecnie około 2 min)
- **Cold start** - < 10s dla pierwszego request po scale-to-zero (dzięki `--cpu-boost`)
- **Memory usage** - < 3GB sustained (4GB limit daje buffer dla peaks)
- **Database query** - P95 < 100ms (obecnie około 65ms)
- **Hybrid search** - P95 < 350ms (obecnie około 280ms)

Metrics są monitorowane przez Cloud Monitoring. Dashboard pokazuje request count, latency percentiles (P50/P90/P95/P99), error rate, CPU/memory utilization, oraz active instances count.

**Setup alerting policies:**

```bash
# Alert na error rate > 1%
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 1%" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=300s

# Alert na latency P95 > 5s
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Latency" \
  --condition-display-name="P95 latency > 5s" \
  --condition-threshold-value=5000 \
  --condition-threshold-duration=300s
```

### Common Production Issues

**Problem 1: Service timeout podczas startu**
Symptom: Cloud Run deployment sukceeded ale /health zwraca 504 Gateway Timeout
Przyczyna: Aplikacja startuje >4 minuty (Cloud Run limit)
Rozwiązanie: Zwiększyć `--timeout` lub zoptymalizować startup (lazy initialization zamiast eager)

**Problem 2: Database connection failed**
Symptom: Logi pokazują `OperationalError: could not connect to server`
Przyczyna: Źle skonfigurowany `DATABASE_URL_CLOUD` secret lub brak uprawnienia do Cloud SQL
Rozwiązanie: Zweryfikować format connection string (`postgresql+asyncpg://...?host=/cloudsql/...`) i sprawdzić czy service account ma rolę `roles/cloudsql.client`

**Problem 3: Neo4j timeout**
Symptom: `/startup` endpoint pokazuje `"neo4j": "connection_failed"`
Przyczyna: Neo4j AuraDB wymaga `neo4j+s://` URI (nie `bolt://`), lub firewall blokuje Cloud Run IP
Rozwiązanie: Zaktualizować `NEO4J_URI` secret i dodać `0.0.0.0/0` do allowlist w AuraDB Console (Cloud Run ma dynamiczne IPs)

**Problem 4: Frontend 404**
Symptom: `GET /` zwraca 404 Not Found, API działa
Przyczyna: Statyczne pliki frontendu nie zostały skopiowane do Docker image (błąd w Dockerfile.cloudrun)
Rozwiązanie: Zweryfikować `COPY --from=frontend-builder /app/dist /app/static` w Dockerfile i sprawdzić czy `app.mount("/", StaticFiles(directory="static", html=True))` jest w main.py

**Problem 5: Slow LLM responses**
Symptom: Timeout errors przy generowaniu person lub focus groups
Przyczyna: Niewystarczające CPU/RAM lub Gemini API throttling
Rozwiązanie: Zwiększyć `--cpu=4 --memory=8Gi` lub zaimplementować rate limiting + request queuing

**Problem 6: Out of memory (OOM)**
Symptom: Cloud Run logs pokazują `Memory limit exceeded`, instancja crashuje
Przyczyna: Memory leak, zbyt duże embeddings w pamięci, lub niewystarczający limit
Rozwiązanie: Zwiększyć `--memory=8Gi` lub zoptymalizować memory usage (batch processing embeddings, garbage collection)

### Cost Optimization

Dla małego projektu (około 100 users, 1000 requests/day) miesięczne koszty wynoszą około **16-30 USD**:

- Cloud Run (sight): $5-10 - zależne od request count i compute time
- Cloud SQL (db-f1-micro): $10-15 - stały koszt za instancję + storage
- Neo4j AuraDB Free: $0 - darmowy tier do 50k nodes
- Upstash Redis Free: $0 - darmowy tier do 10k requests/day
- Cloud Build: $0-2 - pierwsze 120 minut/dzień są free
- Artifact Registry: $1-3 - storage + egress

Największym kosztem jest Cloud SQL. Dla jeszcze niższych kosztów można rozważyć Cloud SQL Serverless (pay-per-use) lub migrację do managed PostgreSQL od innego providera (Supabase, Neon).

**Cost optimization tips:**

1. **Cloud Run auto-scaling** - dzięki `--min-instances=0` aplikacja scale-uje do zero instancji gdy brak traffic. Płacimy tylko za actual compute time, nie za idle instances. Dla około 1000 requests/day (średnio 500ms/request) to około 8 minut compute time dziennie = $0.20/dzień = $6/miesiąc.

2. **Gemini Flash zamiast Pro** - Flash model kosztuje $0.075/1M input tokens (Pro: $1.25 = 17x drożej). Dla większości operacji (generowanie person, focus group responses) Flash daje wystarczającą jakość. Pro używamy tylko dla complex analysis i summarization.

3. **Redis cache hits** - segment briefs są cache'owane w Redis na 7 dni. Cache hit rate około 80% oznacza 80% mniej wywołań Gemini API = oszczędność około $15-20/miesiąc dla aktywnego użytkowania.

4. **Docker layer caching** - Cloud Build cache'uje Docker layers między buildami z explicit `--cache-from` source. Jeśli `requirements.txt` i `package.json` się nie zmieniły, instalacja dependencies jest skipped = build zajmuje 5-8 minut zamiast 20-25. Mniej compute time = niższe koszty Cloud Build (około $0.50-1.00 oszczędności per build).

---

**Autorzy:** DevOps & Infrastructure Team
**Kontakt:** Slack #infrastructure
**Ostatnia aktualizacja:** 2025-11-03
