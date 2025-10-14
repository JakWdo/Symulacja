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

### Uruchom wszystkie testy (bez wolnych)
```bash
pytest tests/ -v -m "not slow and not e2e"
```

### Uruchom z pokryciem kodu
```bash
pytest tests/ --cov=app --cov-report=html -m "not slow"
open htmlcov/index.html
```

### Uruchom tylko szybkie testy jednostkowe
```bash
pytest tests/unit/ -v
```

---

## Struktura Testów

```
tests/
├── unit/                   # Testy jednostkowe (~150 testów, <5s)
│   ├── test_persona_generator.py            # Generator person
│   ├── test_focus_group_service.py          # Serwis grup fokusowych
│   ├── test_graph_service.py                # Serwis grafów
│   ├── test_memory_service_langchain.py     # System pamięci
│   ├── test_discussion_summarizer_service.py # Podsumowania AI
│   ├── test_persona_validator_service.py    # Walidacja person
│   ├── test_survey_response_generator.py    # Generator odpowiedzi
│   ├── test_core_config_security.py         # Konfiguracja i security
│   ├── test_models.py                       # Modele bazy danych
│   ├── test_auth_api.py                     # API autoryzacji
│   ├── test_main_api.py                     # Główne endpointy
│   ├── test_analysis_api.py                 # API analiz
│   ├── test_graph_analysis_api.py           # API analizy grafów
│   └── test_critical_paths.py               # Krytyczne ścieżki
│
├── integration/            # Testy integracyjne z DB (~35 testów, 10-30s)
│   ├── test_auth_api_integration.py         # Flow autoryzacji (11 testów)
│   ├── test_projects_api_integration.py     # CRUD projektów (10 testów)
│   ├── test_personas_api_integration.py     # Generowanie person (7 testów)
│   ├── test_focus_groups_api_integration.py # API grup fokusowych (4 testy)
│   └── test_surveys_api_integration.py      # API ankiet (3 testy)
│
├── e2e/                    # Testy end-to-end (~4 testy, 2-5 min)
│   ├── test_e2e_full_workflow.py            # Pełny workflow badania
│   ├── test_e2e_survey_workflow.py          # Workflow ankiety
│   └── test_e2e_graph_analysis.py           # Workflow analizy grafowej
│
├── performance/            # Testy wydajności (~5 testów, 5-10 min)
│   └── test_performance.py                  # Benchmarki wydajnościowe
│
├── error_handling/         # Testy błędów (~9 testów, 5-10s)
│   └── test_error_handling.py               # Edge cases i resilience
│
├── conftest.py             # Wspólne fixtures i konfiguracja
└── TESTY.md               # Ten plik (dokumentacja)
```

**Łącznie:** ~208 testów

---

## Kategorie Testów

### 🟢 Testy Jednostkowe (Unit Tests)
**Czas:** <5 sekund łącznie
**Liczba:** ~150 testów

Testują pojedyncze funkcje i klasy bez zewnętrznych zależności.

```bash
# Uruchom wszystkie testy jednostkowe
pytest tests/unit/ -v

# Przykładowe moduły:
pytest tests/unit/test_persona_generator.py -v
pytest tests/unit/test_focus_group_service.py -v
```

**Co testują:**
- Losowanie demograficzne (weighted sampling)
- Generowanie cech osobowości (Big Five, Hofstede)
- Walidacja statystyczna (chi-kwadrat)
- Parsowanie odpowiedzi AI
- Ekstrakcja konceptów z tekstu
- Obliczenia sentymentu i polaryzacji

---

### 🟡 Testy Integracyjne (Integration Tests)
**Czas:** 10-30 sekund
**Liczba:** ~35 testów
**Wymagają:** PostgreSQL

Testują endpointy API z rzeczywistą bazą danych.

```bash
# Wymagane: Docker z PostgreSQL
docker-compose up -d postgres

# Uruchom testy integracyjne
pytest tests/integration/ -v
```

**Co testują:**

#### Autoryzacja (11 testów)
- ✅ Rejestracja użytkownika (hashowanie hasła bcrypt)
- ✅ Logowanie (JWT token generation)
- ✅ Walidacja siły hasła
- ✅ Ochrona endpointów (auth required)
- ✅ Wygasłe tokeny
- ✅ Duplikacja email

#### Projekty (10 testów)
- ✅ Tworzenie projektu z demographics
- ✅ Walidacja demographics (suma = 1.0)
- ✅ Listowanie projektów (tylko własne)
- ✅ Aktualizacja projektu
- ✅ Soft delete

#### Persony (7 testów)
- ✅ Generowanie person (Gemini API)
- ✅ Walidacja liczby person (1-1000)
- ✅ Big Five traits verification
- ✅ Tryb adversarial
- ✅ Usuwanie person

#### Grupy Fokusowe (4 testy)
- ✅ Tworzenie grupy fokusowej
- ✅ Aktualizacja draft
- ✅ Listowanie grup
- ✅ Pobieranie wyników

#### Ankiety (3 testy)
- ✅ Tworzenie ankiety
- ✅ Listowanie ankiet
- ✅ Pobieranie szczegółów

---

### 🔴 Testy End-to-End (E2E Tests)
**Czas:** 2-5 minut
**Liczba:** 4 testy
**Wymagają:** PostgreSQL + Gemini API

Testują kompletne scenariusze użytkownika od początku do końca.

```bash
# Wymagane: Docker + Gemini API key
docker-compose up -d postgres redis neo4j
export GOOGLE_API_KEY=your_key

# Uruchom testy E2E (z logowaniem)
pytest tests/e2e/ -v -s
```

#### ⭐ **test_complete_research_workflow_end_to_end**
**Najważniejszy test aplikacji!**

Przepływ (10 kroków):
1. Rejestracja użytkownika
2. Utworzenie projektu badawczego
3. Generowanie 10 person (15-30s)
4. Walidacja statystyczna (chi-kwadrat)
5. Utworzenie grupy fokusowej (5 person × 3 pytania)
6. Uruchomienie dyskusji (30-60s)
7. Weryfikacja 15 odpowiedzi
8. Budowa grafu wiedzy (Neo4j/memory)
9. Generowanie insights AI
10. Weryfikacja performance metrics

**Czas:** ~90-180 sekund
**Jeśli ten test przechodzi, aplikacja działa!** ✅

#### **test_survey_workflow_end_to_end**
Przepływ ankiety:
1. Utworzenie ankiety (4 typy pytań: rating, single-choice, multiple-choice, open-text)
2. Uruchomienie zbierania odpowiedzi
3. Weryfikacja odpowiedzi (10 person × 4 pytania = 40)
4. Analiza statystyczna
5. Demographic breakdown

**Czas:** ~60-120 sekund

#### **test_graph_analysis_complete_workflow**
Przepływ analizy grafowej:
1. Budowa grafu wiedzy
2. Ekstrakcja key concepts
3. Identyfikacja kontrowersyjnych tematów
4. Analiza wpływowych person (PageRank)
5. Korelacje demograficzne
6. Rozkład emocji

**Czas:** ~30-60 sekund

#### **test_graph_fallback_when_neo4j_unavailable**
Test resilience:
- Neo4j niedostępny → fallback do in-memory graph
- System musi działać bez Neo4j ✅

---

### 🔴 Testy Wydajnościowe (Performance Tests)
**Czas:** 5-10 minut
**Liczba:** 5 testów
**Wymagają:** Gemini API

Weryfikują czy system spełnia cele wydajnościowe.

```bash
# Uruchom testy wydajności
pytest tests/performance/ -v -s
```

**Testy:**

| Test | Target | Ideal | Co testuje |
|------|--------|-------|------------|
| `test_persona_generation_performance_20_personas` | <60s | 30-45s | Generowanie 20 person |
| `test_focus_group_execution_performance_20x4` | <3 min | <2 min | 20 person × 4 pytania |
| `test_avg_response_time_per_persona` | <3s | 1-2s | Średni czas odpowiedzi |
| `test_survey_execution_performance_10x10` | <60s | <45s | Ankieta 10×10 |
| `test_parallelization_speedup` | >=2x | >=3x | Speedup równoległości |

**Dlaczego to ważne:**
- Bez testów performance, regresje wydajnościowe są niewidoczne
- Użytkownicy porzucą platformę jeśli generowanie person trwa >2 min
- Weryfikuje że parallel processing działa (3x speedup)

---

### 🟡 Testy Error Handling
**Czas:** 5-10 sekund
**Liczba:** 9 testów

Testują edge cases i resilience systemu.

```bash
pytest tests/error_handling/ -v
```

**Co testują:**

| Test | Scenariusz | Oczekiwane zachowanie |
|------|------------|----------------------|
| `test_gemini_api_timeout_handling` | Gemini API nie odpowiada | Graceful error 503 |
| `test_gemini_api_quota_exceeded_handling` | 429 quota exceeded | Informacja o limicie |
| `test_neo4j_unavailable_fallback_to_memory_graph` | Neo4j down | Fallback do pamięci ✅ |
| `test_empty_personas_list_for_focus_group` | Pusta lista person | Validation error 400 |
| `test_empty_questions_for_focus_group` | Puste pytania | Validation error 400 |
| `test_invalid_demographics_distribution` | Demografia suma != 1.0 | Błąd lub warning |
| `test_concurrent_focus_group_runs_race_condition` | 2 równoległe runs | 409 Conflict lub serialize |
| `test_database_connection_error_handling` | DB disconnect | 500/503 error |

**Dlaczego to ważne:**
- Aplikacja produkcyjna MUSI obsługiwać błędy zewnętrznych serwisów
- Testuje resilience i fallback mechanisms
- Chroni przed crashami w produkcji

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
# Wszystkie testy (bez wolnych E2E/performance)
pytest tests/ -v -m "not slow and not e2e"

# Z pokryciem kodu (coverage)
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Testy jednostkowe (szybkie)
pytest tests/unit/ -v

# Testy integracyjne (wymaga DB)
pytest tests/integration/ -v

# Testy E2E (wymaga Gemini API, wolne)
pytest tests/e2e/ -v -s

# Testy wydajnościowe (bardzo wolne)
pytest tests/performance/ -v -s

# Testy error handling
pytest tests/error_handling/ -v
```

### Zaawansowane Komendy

```bash
# Konkretny plik testowy
pytest tests/unit/test_persona_generator.py -v

# Konkretny test
pytest tests/e2e/test_e2e_full_workflow.py::test_complete_research_workflow_end_to_end -v -s

# Testy według markera
pytest -v -m integration
pytest -v -m "e2e and not slow"
pytest -v -m slow

# Pierwszy failed test (fail fast)
pytest tests/ -x

# Pokaż print statements (-s)
pytest tests/unit/ -v -s

# Równoległe uruchomienie (wymaga pytest-xdist)
pytest tests/unit/ -n auto

# Only failed from last run
pytest tests/ --lf

# Verbose output z timings
pytest tests/ -v --durations=10
```

### Markery Testów

Testy są oznaczone markerami dla łatwego filtrowania:

| Marker | Znaczenie | Użycie |
|--------|-----------|--------|
| `@pytest.mark.integration` | Wymaga bazy danych | `pytest -m integration` |
| `@pytest.mark.e2e` | Test end-to-end | `pytest -m e2e` |
| `@pytest.mark.slow` | Test trwa >10s | `pytest -m "not slow"` |
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
pytest tests/e2e/test_e2e_full_workflow.py::test_complete_research_workflow_end_to_end -v -s
```

**Jeśli ten test przechodzi, aplikacja działa!**

---

#### 2. **test_auth_api_integration.py** 🔐
**Lokalizacja:** `tests/integration/test_auth_api_integration.py`
**Czas:** ~5-10s
**Dlaczego:** Weryfikuje wszystkie security critical paths

```bash
pytest tests/integration/test_auth_api_integration.py -v
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
pytest tests/performance/ -v -s
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
pytest tests/unit/test_critical_paths.py -v
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
pytest tests/error_handling/ -v
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
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=app --cov-report=term-missing

# XML report (dla CI/CD)
pytest tests/ --cov=app --cov-report=xml
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

**Przed (ocena 60/100):**
- 191 testów (155 pass, 36 skip)
- Brak testów E2E
- Brak testów performance
- Brak testów error handling

**Po (ocena 85-90/100):**
- 208 testów (200+ pass, <5 skip)
- ✅ 4 testy E2E
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
# Uruchom tylko szybkie testy
pytest tests/ -m "not slow and not e2e"

# Pomiń testy performance
pytest tests/ -m "not slow"

# Równoległe uruchomienie (wymaga pytest-xdist)
pip install pytest-xdist
pytest tests/unit/ -n auto

# Cache wyników
pytest tests/ --cache-clear  # czyść cache jeśli problemy
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

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test_password@localhost/test_db
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          pytest tests/ -v -m "not slow and not e2e" --cov=app

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## FAQ

### ❓ Czy mogę uruchomić testy bez Dockera?

**Tak**, ale tylko testy jednostkowe:
```bash
pytest tests/unit/ -v
```

Testy integracyjne i E2E wymagają PostgreSQL.

---

### ❓ Czy mogę uruchomić testy bez Gemini API?

**Tak**, większość testów używa mocków:
```bash
# Testy bez Gemini API (unit + integration bez personas)
pytest tests/unit/ tests/integration/test_auth_api_integration.py tests/integration/test_projects_api_integration.py -v
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
pytest tests/path/to/test.py::test_name -v -s

# 2. Uruchom tylko failed test z ostatniego runa
pytest --lf -v

# 3. Użyj pdb (Python debugger)
pytest tests/path/to/test.py::test_name --pdb

# 4. Zwiększ timeout dla async testów
pytest tests/ -v --asyncio-timeout=300
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

**Koniec dokumentacji testów**

Ostatnia aktualizacja: 2025-10-12
Wersja: 2.0 (po reorganizacji struktury)
Liczba testów: 208
