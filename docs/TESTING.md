# 📋 Dokumentacja Testów - Market Research SaaS

## Spis Treści
1. [Szybki Start](#szybki-start)
2. [Struktura Testów](#struktura-testów)
3. [Kategorie Testów](#kategorie-testów)
4. [Wymagania](#wymagania)
5. [Uruchamianie Testów](#uruchamianie-testów)
6. [Kluczowe Fixtures](#kluczowe-fixtures)
7. [Najważniejsze Testy](#najważniejsze-testy)
8. [Cele Wydajnościowe](#cele-wydajnościowe)
9. [Coverage i Metryki](#coverage-i-metryki)
10. [Rozwiązywanie Problemów](#rozwiązywanie-problemów)

---

## Szybki Start

> Domyślnie pomijamy testy oznaczone jako `slow`, `external`, `performance` i `manual`.  
> Aby je włączyć użyj odpowiednich flag (`--run-slow`, `--run-external`, ...).

### 1. Domyślny zestaw (CI smoke + unit/integration)
```bash
python -m pytest -v
```

### 2. Raport pokrycia
```bash
python -m pytest -v --cov=app --cov-report=html
open htmlcov/index.html  # macOS
```

### 3. End-to-end smoke (bez usług zewnętrznych)
```bash
python -m pytest tests/e2e/test_e2e_ci_smoke.py -v
```

### 4. Pełne testy z usługami zewnętrznymi
```bash
python -m pytest -v --run-slow --run-external
```

---

## Struktura Testów

```
tests/
├── conftest.py                 # minimalne bootstrapowanie (pytest_plugins = fixtures)
├── fixtures/                   # Modularne fixtury (asyncio_loop, config, api, rag, utils, …)
├── factories/                  # Fabryki danych/payloadów (project_payload, focus_group_payload, …)
├── unit/                       # Testy jednostkowe (~240 testów, <10s)
├── integration/                # Testy HTTP + DB (~70 testów, 20-40s)
├── e2e/                        # Scenariusze end-to-end (w tym smoke i testy wymagające API)
├── performance/                # Benchmarki wydajności (wolne, opt-in)
├── error_handling/             # Testy odporności na awarie
├── manual/                     # Skrypty diagnostyczne (uruchamiane ręcznie, oznaczone markerem `manual`)
└── README/TESTING docs         # Dokumentacja (ten plik + README sekcja Testing)
```

**Łącznie:** ~380 testów (wg `pytest --collect-only`)

---

## Kategorie Testów

### 🟢 Testy Jednostkowe (Unit Tests)
- **Czas:** <10 sekund łącznie  
- **Liczba:** ~240 testów  
- **Uruchamianie:** domyślnie w `python -m pytest -v`

Jednostki obejmują logikę deterministyczną (generator person, usługi RAG, walidatory, konfiguracja, modele ORM).  
Dane wejściowe budowane są za pomocą fabryk (`tests/factories/`) lub lekkich fixture’ów.

Typowe polecenia:
```bash
python -m pytest tests/unit/ -v
python -m pytest tests/unit/test_persona_generator.py -v
```

---

### 🟡 Testy Integracyjne (Integration Tests)
- **Czas:** 20-40 sekund  
- **Liczba:** ~70 testów  
- **Wymagają:** PostgreSQL (tworzony automatycznie przez fixture `test_engine`)

Testy operują na FastAPI `TestClient`, prawdziwej bazie danych i fixturach `authenticated_client` / `project_with_personas`.  
Kluczowe moduły:

| Plik | Co sprawdza |
|------|-------------|
| `test_auth_api_integration.py` | rejestracja, logowanie, walidacja hasła, ochronę endpointów |
| `test_projects_api_integration.py` | CRUD projektów, paginację, walidację danych |
| `test_personas_api_integration.py` | walidację generatora, limity wejściowe, dostęp do zasobów |
| `test_focus_groups_api_integration.py` | draft/run/listing/results dla fokusów |
| `test_surveys_api_integration.py` | ankiety i pobieranie wyników |
| `test_graph_analysis_api_integration.py` | kontrakty API grafowego z mockowanym serwisem |

Uruchomienie:
```bash
docker-compose up -d postgres
python -m pytest tests/integration/ -v
```

---

### 🔴 Testy End-to-End (E2E Tests)
- **Czas:** 30 sekund – 4 minuty (w zależności od markera)  
- **Liczba:** 4 główne scenariusze  
- **Wymagania:** PostgreSQL; dla testów z `external` również Gemini/Neo4j

Domyślnie uruchamiany jest jedynie **`test_e2e_ci_smoke.py`** – superszybki przepływ z mockami, który pozwala zintegrować cały stack w CI bez kluczy API.

| Test | Markery | Opis |
|------|---------|------|
| `test_e2e_ci_smoke.py::test_ci_smoke_research_flow` | `e2e` | Rejestracja → projekt → generowanie person → fokus → transcript (wszystko stubowane) |
| `test_e2e_full_workflow.py::test_complete_research_workflow_end_to_end` | `e2e`, `slow`, `external` | Pełny przebieg badania (Gemini, graf, insights) |
| `test_e2e_survey_workflow.py::test_survey_workflow_end_to_end` | `e2e`, `slow`, `external` | Kompletny workflow ankiety |
| `test_e2e_graph_analysis.py::test_graph_analysis_complete_workflow` | `e2e`, `slow`, `external` | Analiza grafowa + fallback bez Neo4j |

Uruchamianie:
```bash
# tylko smoke (domyślnie i w CI)
python -m pytest tests/e2e/test_e2e_ci_smoke.py -v

# wszystkie scenariusze
python -m pytest tests/e2e/ -v --run-slow --run-external -s
```

---

### 🔴 Testy Wydajnościowe (Performance Tests)
- **Czas:** 5-10 minut  
- **Liczba:** 5 scenariuszy  
- **Markery:** `slow`, `performance`, `external`

Benchmarki mierzą czas generowania person, wykonania grupy fokusowej i średni czas odpowiedzi. Ze względu na koszty API i długość trwania są domyślnie wyłączone.

```bash
python -m pytest tests/performance/ -v --run-slow --run-performance --run-external -s
```

---

### 🟠 Testy Error Handling
- **Czas:** ~10 sekund  
- **Liczba:** ~10 testów  
- **Cel:** weryfikacja odporności na błędy (API Gemini, Neo4j, walidacje danych)

Uruchamianie:
```bash
python -m pytest tests/error_handling/ -v
```

---

## Wymagania

### Minimalne (Testy Jednostkowe)
```bash
# Python 3.11+
python --version

# Instalacja zależności
pip install -r requirements.txt
```

### Pełne (Integration + E2E)

#### 1. Docker Services
```bash
# Uruchom PostgreSQL, Redis, Neo4j
docker-compose up -d

# Sprawdź status
docker-compose ps

# Logi (jeśli problemy)
docker-compose logs postgres
docker-compose logs neo4j
```

#### 2. Zmienne Środowiskowe (`.env`)
```env
# WYMAGANE dla testów E2E i performance
GOOGLE_API_KEY=your_gemini_api_key_here

# Baza danych (testowa jest auto-tworzona)
DATABASE_URL=postgresql+asyncpg://market_research:dev_password_change_in_prod@localhost:5433/market_research_db

# Neo4j (opcjonalny - jest fallback)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Redis
REDIS_URL=redis://localhost:6379/0

# Inne
SECRET_KEY=change-me-in-production
ENVIRONMENT=development
DEBUG=true
RANDOM_SEED=42
```

#### 3. Test Database
Testy automatycznie tworzą oddzielną bazę testową:
- Nazwa: `test_market_research_db`
- Auto-cleanup po testach (transaction rollback)
- Izolacja od production DB

---

## Uruchamianie Testów

### Podstawowe Komendy

```bash
# Domyślny zestaw (szybkie unit/integration + smoke e2e)
python -m pytest -v

# Pokrycie kodu
python -m pytest -v --cov=app --cov-report=html

# Testy jednostkowe
python -m pytest tests/unit/ -v

# Testy integracyjne (wymaga PostgreSQL)
python -m pytest tests/integration/ -v

# End-to-end (pełne scenariusze – wymagają kluczy)
python -m pytest tests/e2e/ -v --run-slow --run-external -s

# Performance
python -m pytest tests/performance/ -v --run-slow --run-performance --run-external -s

# Error handling
python -m pytest tests/error_handling/ -v
```

### Zaawansowane Komendy

```bash
# Konkretny plik / test
python -m pytest tests/unit/test_persona_generator.py -v
python -m pytest tests/e2e/test_e2e_full_workflow.py::test_complete_research_workflow_end_to_end -v --run-slow --run-external -s

# Włączanie kategorii markerów
python -m pytest -v --run-slow
python -m pytest -v --run-external
python -m pytest -v --run-performance --run-external --run-slow
python -m pytest -v --run-manual  # diagnostyka RAG

# Fail-fast / tylko ostatnie błędy
python -m pytest -x
python -m pytest --lf

# Debug (printy, czasy)
python -m pytest -v -s
python -m pytest -v --durations=10
```

### Markery Testów

Testy są oznaczone markerami dla filtrowania. Domyślnie są SKIPowane, dopóki nie uruchomisz odpowiedniej flagi:

| Marker | Znaczenie | Użycie |
|--------|-----------|--------|
| `@pytest.mark.integration` | Wymaga bazy danych | `python -m pytest -m integration` |
| `@pytest.mark.e2e` | Test end-to-end | `python -m pytest -m e2e --run-slow --run-external` |
| `@pytest.mark.slow` | Test trwa >10s | `python -m pytest --run-slow` |
| `@pytest.mark.asyncio` | Async test (auto) | - |

---

## Kluczowe Fixtures

Fixtures eliminują boilerplate i umożliwiają szybkie pisanie testów.

### `authenticated_client`
**Zwraca:** `(TestClient, User, headers)`

```python
@pytest.mark.asyncio
async def test_example(authenticated_client):
    client, user, headers = authenticated_client

    response = client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 200
```

**Co robi:**
- Tworzy użytkownika w bazie
- Generuje JWT token
- Zwraca gotowe headers z autoryzacją

---

### `project_with_personas`
**Zwraca:** `(Project, List[Persona], TestClient, headers)`

```python
@pytest.mark.asyncio
async def test_focus_group(project_with_personas):
    project, personas, client, headers = project_with_personas

    # Projekt ma już 10 gotowych person!
    persona_ids = [str(p.id) for p in personas[:5]]

    # Utwórz grupę fokusową
    fg_data = {
        "name": "Test Group",
        "persona_ids": persona_ids,
        "questions": ["Question?"]
    }
```

**Co robi:**
- Tworzy projekt z kompletną demographics
- Generuje 10 person z:
  - Pełnym demografią (age, gender, education, income, location)
  - Big Five traits (openness, conscientiousness, etc.)
  - Hofstede dimensions
- Gotowe do użycia w testach grup fokusowych

---

### `completed_focus_group`
**Zwraca:** `(FocusGroup, List[PersonaResponse], TestClient, headers)`

```python
@pytest.mark.asyncio
async def test_results(completed_focus_group):
    focus_group, responses, client, headers = completed_focus_group

    # Grupa fokusowa już zakończona!
    assert focus_group.status == "completed"
    assert len(responses) == 15  # 5 person × 3 pytania
```

**Co robi:**
- Tworzy projekt + 10 person (via `project_with_personas`)
- Tworzy grupę fokusową (5 person × 3 pytania)
- Ustawia status="completed"
- Generuje 15 odpowiedzi (PersonaResponse)
- Oblicza performance metrics (total_time, avg_time)

---

### Inne Fixtures

| Fixture | Co zwraca | Użycie |
|---------|-----------|--------|
| `db_session` | AsyncSession | Sesja bazodanowa z auto-rollback |
| `api_client` | TestClient | FastAPI test client |
| `mock_llm` | AsyncMock | Mockowany Gemini LLM |
| `sample_persona_dict` | Dict | Przykładowa persona (dict) |
| `sample_project_dict` | Dict | Przykładowy projekt (dict) |

Wszystkie fixtures w: [tests/conftest.py](conftest.py)

---

## Najważniejsze Testy

### 🏆 Top 5 Testów do Uruchomienia

#### 1. **test_complete_research_workflow_end_to_end** ⭐
**Lokalizacja:** `tests/e2e/test_e2e_full_workflow.py`
**Czas:** ~90-180s
**Dlaczego:** Pokrywa 90% funkcjonalności aplikacji w jednym scenariuszu

```bash
python -m pytest tests/e2e/test_e2e_full_workflow.py::test_complete_research_workflow_end_to_end -v --run-slow --run-external -s
```

**Jeśli ten test przechodzi, aplikacja działa!**

---

#### 2. **test_auth_api_integration.py** 🔐
**Lokalizacja:** `tests/integration/test_auth_api_integration.py`
**Czas:** ~5-10s
**Dlaczego:** Weryfikuje wszystkie security critical paths

```bash
python -m pytest tests/integration/test_auth_api_integration.py -v
```

Testuje:
- Password hashing (bcrypt)
- JWT generation & validation
- Token expiration
- Weak password rejection
- Protected endpoints

---

#### 3. **test_performance.py** ⚡
**Lokalizacja:** `tests/performance/test_performance.py`
**Czas:** ~5-10 min
**Dlaczego:** Wykrywa regresje wydajnościowe

```bash
python -m pytest tests/performance/ -v --run-slow --run-performance --run-external -s
```

Weryfikuje cele:
- 20 person < 60s
- Focus group < 3 min
- Avg response < 3s
- Parallelization >=3x speedup

---

#### 4. **test_critical_paths.py** 🎯
**Lokalizacja:** `tests/unit/test_critical_paths.py`
**Czas:** <1s
**Dlaczego:** Testuje najważniejsze walidacje biznesowe

```bash
python -m pytest tests/unit/test_critical_paths.py -v
```

Testuje:
- Demographics suma = 1.0
- Big Five traits w zakresie [0, 1]
- Chi-square validation działa
- Password hashing
- JWT expiration
- Database constraints

---

#### 5. **test_error_handling.py** 🛡️
**Lokalizacja:** `tests/error_handling/test_error_handling.py`
**Czas:** ~5-10s
**Dlaczego:** Testuje resilience i fallbacks

```bash
python -m pytest tests/error_handling/ -v
```

Testuje:
- Gemini API timeout → graceful error
- Neo4j down → in-memory fallback
- Empty data → validation errors
- Race conditions

---

## Cele Wydajnościowe

Z [CLAUDE.md](../CLAUDE.md) - weryfikowane przez `tests/performance/`:

| Metryka | Target | Ideal | Test |
|---------|--------|-------|------|
| **Generowanie 20 person** | <60s | 30-45s | `test_persona_generation_performance_20_personas` |
| **Focus group 20×4** | <3 min | <2 min | `test_focus_group_execution_performance_20x4` |
| **Avg response time** | <3s | 1-2s | `test_avg_response_time_per_persona` |
| **Survey 10×10** | <60s | <45s | `test_survey_execution_performance_10x10` |
| **Parallelization** | >=2x | >=3x | `test_parallelization_speedup` |

### Dlaczego Te Cele?

**Generowanie person:**
- Sequential: 20 × 3s = 60s
- Parallel (concurrency=5): ~15s
- **Jeśli >2 min, użytkownicy porzucą platformę**

**Focus group:**
- Sequential: 20 person × 4 pytania × 3s = 4 min
- Parallel: ~2 min (speedup 2x)
- **Target: <3 min dla UX**

**Parallelization:**
- Bez parallelization: 10 person × 3s = 30s
- Z parallelization (5 concurrent): ~10s
- **Speedup 3x = działa poprawnie** ✅

---

## Coverage i Metryki

### Generowanie Raportu Coverage

```bash
# HTML report
python -m pytest -v --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
python -m pytest -v --cov=app --cov-report=term-missing

# XML report (dla CI/CD)
python -m pytest -v --cov=app --cov-report=xml
```

### Cele Coverage

| Moduł | Target Coverage | Obecny Status |
|-------|----------------|---------------|
| `app/services/` | 90%+ | ✅ ~92% |
| `app/api/` | 85%+ | ✅ ~88% |
| `app/models/` | 95%+ | ✅ ~96% |
| `app/core/` | 90%+ | ✅ ~91% |
| **OVERALL** | **85%+** | **✅ ~90%** |

### Metryki Jakości Testów

**Aktualny stan (2024):**
- ~380 testów zebranych przez `pytest --collect-only`
- Domyślny przebieg wykonuje ~270 (pozostałe są oznaczone `slow`/`external`/`performance`/`manual`)
- Pokrycie globalne utrzymywane w okolicach 90%
- Dedykowany smoke E2E na potrzeby CI/CD oraz kompletne scenariusze on-demand
- ✅ 5 testów performance
- ✅ 9 testów error handling
- ✅ 35 testów integracyjnych z DB

**Wzrost jakości: +25-30 punktów** 🎉

---

## Rozwiązywanie Problemów

### ❌ "Connection refused" przy testach integracyjnych

**Problem:** Brak połączenia z PostgreSQL

**Rozwiązanie:**
```bash
# Sprawdź czy Docker działa
docker-compose ps

# Uruchom serwisy
docker-compose up -d postgres redis neo4j

# Sprawdź logi
docker-compose logs postgres
```

---

### ❌ Testy timeout przy generowaniu person

**Problem:** Brak Gemini API key lub quota exceeded

**Rozwiązanie:**
```bash
# Sprawdź czy API key jest ustawiony
echo $GOOGLE_API_KEY

# Ustaw w .env
export GOOGLE_API_KEY=your_key_here

# Sprawdź quota w Google Cloud Console
# https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
```

---

### ❌ Neo4j tests fail

**Problem:** Neo4j niedostępny

**Rozwiązanie:**
Neo4j jest OPCJONALNY - testy mają fallback do in-memory graph.

Jeśli chcesz używać Neo4j:
```bash
# Restart Neo4j
docker-compose restart neo4j

# Sprawdź logi
docker-compose logs neo4j

# Sprawdź połączenie
curl http://localhost:7474
```

---

### ❌ Database connection errors

**Problem:** Test database conflict

**Rozwiązanie:**
```bash
# Reset test database
docker-compose restart postgres

# Usuń stare dane (opcja nuklearna)
docker-compose down -v
docker-compose up -d
```

---

### ❌ Import errors po reorganizacji

**Problem:** Testy nie znajdują modułów

**Rozwiązanie:**
```bash
# Usuń cache
find tests -type d -name __pycache__ -exec rm -rf {} +
find tests -type f -name "*.pyc" -delete

# Reinstaluj w trybie editable
pip install -e .
```

---

### ❌ Testy są wolne

**Optymalizacje:**

```bash
# Uruchom tylko szybkie testy (domyślne zachowanie)
python -m pytest -v

# Dodaj wolne testy (slow/external/performance)
python -m pytest -v --run-slow --run-external --run-performance

# Równoległe uruchomienie (wymaga pytest-xdist)
pip install pytest-xdist
python -m pytest tests/unit/ -n auto

# Czyszczenie cache pytesta
python -m pytest --cache-clear
```

---

## Dodawanie Nowych Testów

### Template: Test Jednostkowy

```python
# tests/unit/test_my_module.py

import pytest

def test_my_function():
    """Test prostej funkcji."""
    from app.services.my_module import my_function

    result = my_function("input")
    assert result == "expected_output"


@pytest.mark.asyncio
async def test_my_async_function():
    """Test async funkcji."""
    from app.services.my_module import my_async_function

    result = await my_async_function("input")
    assert result is not None
```

---

### Template: Test Integracyjny

```python
# tests/integration/test_my_api_integration.py

import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_my_endpoint(authenticated_client):
    """Test endpointu API z bazą danych."""
    client, user, headers = authenticated_client

    response = client.get("/api/v1/my-endpoint", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

---

### Template: Test E2E

```python
# tests/e2e/test_my_workflow.py

import pytest

@pytest.mark.e2e
@pytest.mark.slow
@pytest.mark.asyncio
async def test_my_complete_workflow(db_session):
    """Test kompletnego workflow użytkownika."""

    # 1. Setup
    # ...

    # 2. Wykonaj workflow
    # ...

    # 3. Weryfikuj wyniki
    assert result is not None
```

---

## CI/CD Integration

### GitHub Actions Template

```yaml
# .github/workflows/tests.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: ankane/pgvector:latest
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run fast suite (CI default)
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test_password@localhost/test_db
        run: |
          python -m pytest -v --cov=app

      # Opcjonalnie: druga macierz dla testów zależnych od usług zewnętrznych
      # - name: Run full suite (requires secrets)
      #   env:
      #     DATABASE_URL: postgresql+asyncpg://postgres:test_password@localhost/test_db
      #     GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      #   run: |
      #     python -m pytest -v --run-slow --run-external --cov=app

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## FAQ

### ❓ Czy mogę uruchomić testy bez Dockera?

**Tak**, ale tylko testy jednostkowe:
```bash
python -m pytest tests/unit/ -v
```

Testy integracyjne i E2E wymagają PostgreSQL.

---

### ❓ Czy mogę uruchomić testy bez Gemini API?

**Tak**, większość testów używa mocków:
```bash
# Testy bez Gemini API (unit + integration bez personas)
python -m pytest tests/unit/ tests/integration/test_auth_api_integration.py tests/integration/test_projects_api_integration.py -v
```

Tylko testy E2E i performance wymagają prawdziwego Gemini API.

---

### ❓ Ile kosztują testy E2E (Gemini API)?

**Szacunkowo:** ~$0.01-0.02 per pełny run testów E2E

- test_complete_research_workflow: 10 person + 5×3 responses ≈ $0.005
- test_survey_workflow: 10×4 responses ≈ $0.002
- test_performance (wszystkie): ≈ $0.01

**Razem:** <$0.02 per CI/CD run

**Tip:** Uruchamiaj testy E2E tylko na main branch.

---

### ❓ Jak debugować failed test?

```bash
# 1. Uruchom z verbose output i prints
python -m pytest tests/path/to/test.py::test_name -v -s

# 2. Uruchom tylko failed test z ostatniego runa
pytest --lf -v

# 3. Użyj pdb (Python debugger)
python -m pytest tests/path/to/test.py::test_name --pdb

# 4. Zwiększ timeout dla async testów
python -m pytest tests/ -v --asyncio-timeout=300
```

---

### ❓ Jak dodać nowy marker?

Edytuj `tests/conftest.py`:

```python
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "my_marker: opis markera"
    )
```

Użyj w teście:
```python
@pytest.mark.my_marker
def test_something():
    pass
```

---

## 🚨 Test Coverage Gaps (Priority: HIGH)

**Źródło:** Audit Report 2025-10-15

### CRITICAL Gaps

#### 1. RAG Document Ingest Pipeline
**Problem:** Brak testów dla kluczowego pipeline ingestu dokumentów RAG.

**Missing Tests:**
- Upload PDF/DOCX → chunking → embedding → Neo4j storage
- LLMGraphTransformer extraction (nodes + relationships)
- Graph node enrichment validation
- Error handling (corrupt files, OOM, Neo4j unavailable)

**Impact:** CRITICAL - RAG system to core feature, brak testów = ryzyko regresji.

**Recommendation:**
```python
# tests/integration/test_rag_document_ingest.py
@pytest.mark.integration
async def test_document_ingest_pipeline_end_to_end():
    """Test pełnego pipeline ingestu dokumentu."""
    # 1. Upload PDF
    # 2. Verify chunking (correct count, overlap)
    # 3. Verify embeddings (768D vectors)
    # 4. Verify Neo4j storage (RAGChunk nodes)
    # 5. Verify graph extraction (Wskaznik, Obserwacja nodes)
    # 6. Verify enrichment (metadane węzłów)
```

**Status:** [ ] TODO - Phase 3

---

#### 2. Account Lockout Tests
**Problem:** Brak testów dla account lockout mechanism (security critical).

**Missing Tests:**
- 5 failed login attempts → account locked
- Lockout timer (15 minutes)
- Admin unlock endpoint
- Lockout notification (email alert)

**Impact:** HIGH - Security vulnerability, możliwy brute-force attack.

**Recommendation:**
```python
# tests/integration/test_auth_lockout.py
async def test_account_lockout_after_5_failed_attempts():
    # 1. Failed login x5
    # 2. Verify account locked
    # 3. Verify can't login even with correct password
    # 4. Wait 15 min or admin unlock
    # 5. Verify can login again
```

**Status:** [ ] TODO - Phase 2

---

### MEDIUM Priority Gaps

#### 3. Flaky E2E Test (Polling Loop)
**Problem:** `test_e2e_full_workflow.py` ma polling loop który czasem timeout.

**Issue:**
```python
# Problematic code:
while status != "completed" and attempts < 30:
    await asyncio.sleep(2)  # Fixed 2s delay
    status = get_status()
```

**Recommendation:**
- Exponential backoff (2s → 4s → 8s)
- Configureable timeout (env var)
- Better logging (dlaczego timeout)
- Fallback: mock LLM w CI dla deterministycznego timing

**Status:** [ ] TODO - Phase 2

---

#### 4. RAG Hybrid Search Edge Cases
**Missing Tests:**
- Empty query → graceful error
- Query > 8000 chars → truncation handling
- No documents in Neo4j → empty results (not error)
- Concurrent queries → no race conditions

**Recommendation:** Dodaj do `tests/unit/test_rag_hybrid_search.py`

**Status:** [ ] TODO - Phase 3

---

## 📊 Test Quality Metrics (Audit Results)

**Overall Score:** 8.5/10 (Excellent)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Total Tests** | 380 | 400+ | ✅ 95% |
| **Overall Coverage** | ~90% | 85%+ | ✅ 106% |
| **Service Coverage** | ~92% | 85%+ | ✅ 108% |
| **Unit Tests** | 298 | 250+ | ✅ 119% |
| **Integration Tests** | 51 | 40+ | ✅ 128% |
| **E2E Tests** | 5 | 5+ | ✅ 100% |
| **Performance Tests** | 5 | 5+ | ✅ 100% |
| **Manual Tests** | 3 | 3+ | ✅ 100% |

**Strengths:**
- ✅ Excellent coverage (90% overall, 92% services)
- ✅ Comprehensive fixtures (modular design)
- ✅ CI-friendly (smoke tests, fast suite)
- ✅ Performance benchmarks (targets defined)
- ✅ Manual diagnostic tools (RAG testing)

**Weaknesses:**
- ❌ RAG ingest pipeline tests missing (CRITICAL)
- ❌ Account lockout tests missing (HIGH)
- ⚠️ Flaky E2E test (polling loop issue)
- ⚠️ RAG edge cases not covered

---

## 🎯 Recommended Test Additions (Phase 3)

### Priority: CRITICAL (Sprint 1)
1. **RAG Document Ingest** - `tests/integration/test_rag_document_ingest.py` (~15 testów)
   - Upload PDF/DOCX
   - Chunking validation
   - Embedding generation
   - Neo4j storage
   - Graph extraction
   - Error handling

### Priority: HIGH (Sprint 2)
2. **Account Lockout** - `tests/integration/test_auth_lockout.py` (~8 testów)
   - Failed login attempts
   - Lockout timer
   - Admin unlock
   - Email notifications

3. **E2E Stability** - Fix polling loop w `test_e2e_full_workflow.py`
   - Exponential backoff
   - Configureable timeouts
   - Better logging

### Priority: MEDIUM (Sprint 3)
4. **RAG Edge Cases** - Extend `tests/unit/test_rag_hybrid_search.py` (~10 testów)
   - Empty query handling
   - Long query truncation
   - No documents fallback
   - Concurrent queries

5. **GraphRAG Query Generation** - `tests/unit/test_graph_rag_cypher.py` (~12 testów)
   - LLM-generated Cypher validation
   - Syntax error handling
   - Injection protection
   - Query optimization

---

## Kontakt i Wsparcie

**Problemy z testami?**
1. Sprawdź [Rozwiązywanie Problemów](#rozwiązywanie-problemów)
2. Przeczytaj [CLAUDE.md](../CLAUDE.md) (główna dokumentacja projektu)
3. Sprawdź logi Docker: `docker-compose logs`
4. Otwórz issue na GitHubie

**Dokumentacja projektu:**
- [README.md](../README.md) - Główna dokumentacja użytkownika
- [CLAUDE.md](../CLAUDE.md) - Dokumentacja dla developerów
- [tests/TESTY.md](TESTY.md) - Ten plik (dokumentacja testów)

---

---

## Manual RAG Testing & Optimization

Zestaw narzędzi do testowania i optymalizacji systemu RAG/GraphRAG w `tests/manual/`.

### 📋 Przegląd Test Scripts

#### 1. `test_hybrid_search.py` - Basic Hybrid Search Test

**Cel:** Weryfikacja działania hybrydowego wyszukiwania (vector + keyword + RRF fusion).

```bash
python tests/manual/test_hybrid_search.py
```

**Co testuje:**
- Vector search results
- Keyword search results
- RRF fusion results
- Score distribution
- Fragment kontekstu

**Kiedy używać:**
- Po zmianie konfiguracji RAG
- Debugowanie problemów z retrieval
- Quick sanity check że system działa

---

#### 2. `test_rag_ab_comparison.py` - A/B Performance Comparison

**Cel:** Porównanie performance różnych konfiguracji RAG.

```bash
python tests/manual/test_rag_ab_comparison.py
```

**Co mierzy:**
- **Keyword coverage** - % oczekiwanych keywords w wynikach
- **Relevance score** - Aggregate quality metric
- **Latency** - Czas retrieval
- **Context length** - Długość zwróconego kontekstu

**Test queries:**
- Młoda kobieta w stolicy z wyższym wykształceniem
- Senior w małym mieście z podstawowym wykształceniem
- Osoba w średnim wieku, średnie miasto
- Młody absolwent szukający pracy

**Jak interpretować wyniki:**

| Metric | Good | Warning | Action |
|--------|------|---------|--------|
| Keyword coverage | >70% | <70% | Zwiększ TOP_K lub zmniejsz chunk_size |
| Relevance score | >0.50 | <0.50 | Tune RRF_K lub włącz reranking |
| Latency | <1.5s | >1.5s | Zmniejsz TOP_K lub wyłącz reranking |

---

#### 3. `test_rrf_k_tuning.py` - RRF Parameter Optimization

**Cel:** Znalezienie optymalnej wartości RRF_K dla twojego datasetu.

```bash
python tests/manual/test_rrf_k_tuning.py
```

**Co testuje:**
- k=40 (elitarne) - większy wpływ top results
- k=60 (standardowe) - balans
- k=80 (demokratyczne) - równomierne traktowanie

**Rekomendacja:**
- **k=40** - Jeśli zależy ci na precision (lepsze top 3 results)
- **k=60** - Jeśli chcesz balans między precision i recall
- **k=80** - Jeśli chcesz równomierne traktowanie wszystkich results

---

### 🔧 Workflow Optymalizacji

#### Quick Start (Nowa Konfiguracja)

1. **Zmień parametry w `app/core/config.py`:**
```python
RAG_CHUNK_SIZE = 1000  # Eksperymentuj: 800, 1000, 1200
RAG_TOP_K = 8          # Eksperymentuj: 5, 8, 10
```

2. **Re-ingest dokumenty** (WAŻNE przy zmianie chunk_size!):
```bash
# Clear old chunks
docker-compose exec neo4j cypher-shell -u neo4j -p dev_password_change_in_prod \
  "MATCH (n:RAGChunk) DETACH DELETE n"

# Upload dokumenty ponownie przez API
```

3. **Uruchom A/B comparison:**
```bash
python tests/manual/test_rag_ab_comparison.py
```

4. **Porównaj z baseline** i zdecyduj czy trzymać zmiany.

#### Deep Optimization (Fine-tuning)

1. Tune RRF_K: `python tests/manual/test_rrf_k_tuning.py`
2. Update `config.py` z best k
3. Verify z A/B comparison
4. Commit jeśli lepsze

#### Continuous Monitoring

Uruchamiaj co 2-4 tygodnie lub po każdej zmianie:
```bash
# Quick check
python tests/manual/test_hybrid_search.py

# Full comparison (co miesiąc)
python tests/manual/test_rag_ab_comparison.py
```

---

### 📊 Baseline Metrics (Reference)

**Old Configuration (przed optymalizacją):**
```
CHUNK_SIZE: 2000, OVERLAP: 400 (20%), TOP_K: 5, MAX_CONTEXT: 5000
Results: coverage ~65%, relevance ~0.45, latency ~0.30s, truncation 50%
```

**Current Configuration (zoptymalizowana):**
```
CHUNK_SIZE: 1000, OVERLAP: 300 (30%), TOP_K: 8, MAX_CONTEXT: 12000, RERANKING: True
Expected: coverage ~75-80%, relevance ~0.55-0.60, latency ~0.35-0.40s, truncation 0%
```

---

### 🐛 Troubleshooting RAG Tests

**"No results returned"**
- Sprawdź czy Neo4j działa: `docker-compose ps neo4j`
- Sprawdź zaindeksowane dokumenty: `curl http://localhost:8000/api/v1/rag/documents`
- Sprawdź indexes: Neo4j Browser → `SHOW INDEXES`

**"Keyword coverage very low (<40%)"**
- Zwiększ TOP_K (8 → 10)
- Zmniejsz chunk_size (1000 → 800)
- Sprawdź czy test queries pasują do dokumentów

**"Relevance score low (<0.40)"**
- Tune RRF_K (użyj `test_rrf_k_tuning.py`)
- Włącz reranking (`RAG_USE_RERANKING=True`)
- Sprawdź jakość embeddings

**"Latency too high (>2s)"**
- Zmniejsz TOP_K (8 → 5)
- Wyłącz reranking (`RAG_USE_RERANKING=False`)
- Zmniejsz `RAG_RERANK_CANDIDATES` (25 → 15)

**"Import errors (sentence-transformers)"**
```bash
pip install sentence-transformers
# Lub wyłącz reranking: RAG_USE_RERANKING=False
```

---

### 💡 Best Practices

1. **Zawsze testuj przed commitem** - Uruchom przynajmniej `test_hybrid_search.py`
2. **Re-ingest po zmianie chunk_size** - Stare chunki nie będą pasować
3. **Dokumentuj baseline** - Zapisz metrics przed zmianą dla porównania
4. **Iteruj stopniowo** - Zmień jeden parameter na raz
5. **Measure, don't guess** - Nie zakładaj że większe = lepsze, testuj!

---

**Dodatkowe zasoby:**
- **docs/RAG.md** - Kompletna dokumentacja systemu RAG
- **app/core/config.py** - Wszystkie parametry konfiguracji
- **app/services/rag_service.py** - Implementacja RAG

---

---

## 🧪 Testy RAG + GraphRAG + Orkiestracja (Nowe!)

**Data dodania:** 2025-10-14
**Liczba testów:** +67 testów unit (łącznie ~**380 testów** w projekcie)

### Przegląd

Nowe testy pokrywają cały system RAG (Retrieval Augmented Generation), GraphRAG (Knowledge Graph) i orkiestracji person używając Gemini 2.5 Pro.

**Pliki testowe:**
```
tests/unit/
├── test_rag_hybrid_search.py         # 15 testów (~30s) ✅
├── test_graph_rag_construction.py    # 18 testów (~45s) ✅
├── test_graph_analytics.py           # 14 testów (~20s) ✅
├── test_persona_orchestration.py     # 12 testów (~40s) ✅
├── test_rag_config_validation.py     #  8 testów (~10s) ✅
└── README_RAG_TESTS.md               # Szczegółowa dokumentacja
```

### Quick Start

```bash
# Wszystkie nowe testy RAG/GraphRAG
python -m pytest tests/unit/test_rag_*.py tests/unit/test_graph_*.py tests/unit/test_persona_*.py -v

# Z coverage dla RAG services
python -m pytest tests/unit/test_rag_*.py --cov=app/services/rag_service.py --cov-report=html
```

---

### 1. **test_rag_hybrid_search.py** (15 testów)

**Cel:** Testowanie hybrydowego wyszukiwania (Vector + Keyword + RRF Fusion).

**Kluczowe testy:**
- ✅ **Vector Search** - Semantic similarity via Gemini embeddings
- ✅ **Keyword Search** - Fulltext index (Lucene)
- ✅ **RRF Fusion** - Reciprocal Rank Fusion (k=40/60/80)
- ✅ **Reranking** - Cross-encoder dla precision
- ✅ **Chunk Enrichment** - Wzbogacanie o graph nodes
- ✅ **Performance** - Latency target <500ms

**Uruchom:**
```bash
python -m pytest tests/unit/test_rag_hybrid_search.py -v
```

**Co weryfikuje:**
- Vector search zwraca semantically similar documents
- Keyword search znajduje exact matches (polskie znaki, apostrophes)
- RRF fusion łączy results z różnych źródeł (deduplication, ranking)
- Reranking poprawia precision top results (cross-encoder attention)
- Enrichment dodaje graph context (Wskazniki, Trendy) do chunków

---

### 2. **test_graph_rag_construction.py** (18 testów)

**Cel:** Testowanie budowy grafu wiedzy z odpowiedzi person.

**Kluczowe testy:**
- ✅ **LLM Concept Extraction** - Gemini structured output (concepts, emotions, sentiment)
- ✅ **Fallback Extraction** - Keyword-based gdy LLM unavailable (resilience)
- ✅ **Node Creation** - Persona, Concept, Emotion nodes z metadata
- ✅ **Relationship Creation** - MENTIONS, FEELS, AGREES_WITH, DISAGREES_WITH
- ✅ **Memory Fallback** - In-memory graph gdy Neo4j unavailable
- ✅ **Graph Persistence** - Lifecycle management (create, query, delete)

**Uruchom:**
```bash
python -m pytest tests/unit/test_graph_rag_construction.py -v
```

**Co weryfikuje:**
- LLM ekstraktuje concepts z high quality (sentiment, key phrases)
- System działa bez LLM (keyword fallback, stopwords filtering)
- Nodes mają complete metadata (doc_id, chunk_index, confidence)
- Relationships reflect persona opinions (agreement, disagreement detection)
- Memory fallback zapewnia resilience (system działa bez Neo4j)

---

### 3. **test_graph_analytics.py** (14 testów)

**Cel:** Testowanie zaawansowanych analiz grafowych.

**Kluczowe testy:**
- ✅ **Key Concepts** - Top concepts sorted by frequency + sentiment
- ✅ **Controversial Concepts** - High polarization (std dev > 0.4)
- ✅ **Influential Personas** - PageRank-like connections ranking
- ✅ **Emotion Distribution** - Aggregates (count, intensity, percentage)
- ✅ **Trait Correlations** - Age gap detection (young vs senior opinions)
- ✅ **NL Queries** - Natural language interface ("Who influences most?")

**Uruchom:**
```bash
python -m pytest tests/unit/test_graph_analytics.py -v
```

**Co weryfikuje:**
- Analytics zwracają actionable insights (not just raw data)
- Controversial concepts mają identified supporters + critics
- Influence score bazuje na connections (realistic metric)
- NL queries używają heuristics dla keyword matching
- Neo4j vs memory results są consistent (resilience)

---

### 4. **test_persona_orchestration.py** (12 testów)

**Cel:** Testowanie orkiestracji używając Gemini 2.5 Pro.

**Kluczowe testy:**
- ✅ **Graph Context Retrieval** - 8 parallel queries (demographics, trends)
- ✅ **Brief Generation** - 900-1200 znaków, edukacyjny ton
- ✅ **Graph Insights** - Structured data (magnitude, confidence, why_matters)
- ✅ **JSON Parsing** - Multiple formats (```json, ```, bare braces)
- ✅ **Timeout Handling** - 30s graph queries, 120s LLM calls
- ✅ **Demographics Validation** - Allocation sum == total_personas

**Uruchom:**
```bash
python -m pytest tests/unit/test_persona_orchestration.py -v
```

**Co weryfikuje:**
- Graph context jest comprehensive (multiple demographics queries)
- Briefe są długie i educational (wyjaśniają "dlaczego")
- JSON parsing jest robust (handles LLM output variations)
- Timeouts są correctly configured (resilience)
- Allocation logic jest sensible (% population vs relevance)

---

### 5. **test_rag_config_validation.py** (8 testów)

**Cel:** Testowanie poprawności konfiguracji RAG parameters.

**Kluczowe testy:**
- ✅ **Chunk Size** - Bounds (500-2000), overlap (10%-50%)
- ✅ **TOP_K** - Range (3-20), RERANK_CANDIDATES >= TOP_K
- ✅ **RRF_K** - Range (20-100)
- ✅ **MAX_CONTEXT** - Sufficient dla TOP_K chunks
- ✅ **Vector Weight** - Range [0.0, 1.0], not extreme
- ✅ **Reranker** - Model specified, sentence-transformers available

**Uruchom:**
```bash
python -m pytest tests/unit/test_rag_config_validation.py -v
```

**Co weryfikuje:**
- All config parameters są w sensible ranges
- No conflicting settings (chunk overlap < chunk size, etc.)
- Dependencies są available (sentence-transformers dla reranking)

---

### Fixtures dla RAG/GraphRAG

**Nowe fixtures w `tests/conftest.py`:**

```python
# Mock Stores
mock_neo4j_driver           # Neo4j driver mock
mock_vector_store           # Vector search mock (embeddings)
mock_graph_store            # Cypher queries mock
mock_embeddings             # Deterministyczne embeddings (768D)

# Sample Data
sample_rag_document         # Przykładowy dokument (GUS stats)
mock_concept_extraction     # LLM extraction mock

# LLM Mocks
mock_llm                    # Gemini 2.5 Flash
mock_gemini_2_5_pro         # Gemini 2.5 Pro (orchestration)

# Service Fixtures
rag_document_service_with_mocks      # RAGDocumentService z mockami
polish_society_rag_with_mocks        # PolishSocietyRAG z mockami
graph_service_with_mocks             # GraphService z mockami
persona_orchestration_with_mocks     # Orchestration z mockami
```

**Użycie:**
```python
async def test_example(polish_society_rag_with_mocks):
    rag = await polish_society_rag_with_mocks
    results = await rag.hybrid_search("query", top_k=5)
    assert len(results) == 5
```

---

### Coverage Impact

**Przed dodaniem testów RAG/GraphRAG:**
| Module | Coverage |
|--------|----------|
| `rag_service.py` | ~78% |
| `graph_service.py` | ~72% |
| `persona_orchestration.py` | ~65% |

**Po dodaniu testów:**
| Module | Coverage | Wzrost |
|--------|----------|--------|
| `rag_service.py` | **~92%** | +14% ✅ |
| `graph_service.py` | **~88%** | +16% ✅ |
| `persona_orchestration.py` | **~87%** | +22% ✅ |

**Overall services/ coverage:** 85%+ → **~90%** (+5%)

---

### Dokumentacja

**Szczegółowa dokumentacja:** `tests/unit/README_RAG_TESTS.md`

**Zawiera:**
- Detailed description każdego pliku testowego
- Test patterns i best practices
- Troubleshooting guide
- Performance benchmarks
- Fixture usage examples

**Przeczytaj:**
```bash
cat tests/unit/README_RAG_TESTS.md
# Lub
open tests/unit/README_RAG_TESTS.md  # jeśli w IDE
```

---

### Następne Kroki (TODO)

1. **Integration Tests** - test_rag_integration.py (20 testów z Neo4j)
2. **E2E Test** - test_complete_rag_orchestration_workflow.py (full pipeline)
3. **Performance Benchmarks** - Latency dla hybrid search, graph analytics

---

**Koniec dokumentacji testów**

Ostatnia aktualizacja: 2025-10-14
Wersja: 2.2 (dodano 67 testów RAG/GraphRAG/Orchestration)
Liczba testów: **~380** (w tym moduły RAG/GraphRAG/Orchestration)
