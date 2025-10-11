# 🧪 JAK TESTOWAĆ - Market Research SaaS

> **Kompletny przewodnik testowania aplikacji**

---

## 📋 Spis treści

1. [Szybki start - uruchom wszystko](#-szybki-start)
2. [Struktura testów](#-struktura-testów)
3. [Wyniki i metryki](#-obecne-wyniki)
4. [Uruchamianie testów](#-uruchamianie-testów)
5. [Testy wymagające środowiska](#-testy-wymagające-środowiska)
6. [Fixtures i konfiguracja](#-fixtures-conftest)
7. [Dodawanie nowych testów](#-dodawanie-nowych-testów)
8. [CI/CD Integration](#-cicd-github-actions)
9. [Debugging i troubleshooting](#-debugging)
10. [FAQ](#-faq)

---

## 🚀 Szybki start

### Instalacja zależności
```bash
pip install pytest pytest-asyncio pytest-cov email-validator
```

### Uruchom WSZYSTKIE działające testy jedną komendą
```bash
# Opcja 1: Tylko testy jednostkowe (bez środowiska) - 95 testów
python -m pytest tests/ -v

# Opcja 2: Z coverage
python -m pytest tests/ --cov=app --cov-report=html

# Opcja 3: Tylko szybkie testy (<2s)
python -m pytest tests/ -v -m "not slow"

# Opcja 4: Parallel execution (szybciej)
pip install pytest-xdist
python -m pytest tests/ -n auto
```

### Uruchom testy według kategorii
```bash
# Tylko testy krytyczne (najważniejsze)
python -m pytest tests/test_critical_paths.py -v

# Tylko security & auth
python -m pytest tests/test_core_config_security.py tests/test_auth_api.py -v

# Tylko serwisy core
python -m pytest tests/test_persona_generator.py tests/test_memory_service_langchain.py -v

# Tylko API
python -m pytest tests/test_main_api.py tests/test_api_integration.py -v
```

---

## 📂 Struktura testów

```
tests/
├── JAK_TESTOWAĆ.md              ← TEN PLIK
├── conftest.py                   ← Fixtures i konfiguracja pytest
├── __init__.py                   ← Definicje kategorii testów
│
├── test_critical_paths.py        ✅ 21 testów - KRYTYCZNE ścieżki biznesowe
├── test_core_config_security.py  ✅ 6 testów - Security & config
├── test_persona_generator.py     ✅ 6 testów - Generowanie person
├── test_persona_validator_service.py ✅ 4 testy - Walidacja person
├── test_memory_service_langchain.py ✅ 4 testy - Event sourcing
├── test_discussion_summarizer_service.py ✅ 4 testy - AI summaries
├── test_analysis_api.py          ✅ 6 testów - Insights API (nowe)
├── test_graph_analysis_api.py    ✅ 11 testów - Graph analytics API (nowe)
├── test_auth_api.py              ✅ 30 testów - Autentykacja
├── test_main_api.py              ✅ 3 testy - Podstawowe API
├── test_api_integration.py       ✅ 7 testów - Walidacja payloadów
│
├── test_models.py                ⚠️ 26 testów - Database models
├── test_focus_group_service.py   🔧 11 testów - Focus groups
├── test_graph_service.py         🔧 17 testów - Graph analysis
├── test_survey_response_generator.py 🔧 17 testów - Surveys
└── test_e2e_integration.py       📋 20 testów - E2E scenarios (skipped)
```

**Legenda:**
- ✅ = Działają bez dodatkowej konfiguracji (95 testów)
- ⚠️ = Niektóre failują, wymagają fixów
- 🔧 = Wymagają dopasowania do API serwisów
- 📋 = Szkielety dokumentacyjne (skipped)

---

## 📊 Obecne wyniki

### Statystyki
- **Łącznie testów:** 202
- **Przechodzących:** 95 (100% unit tests, w tym analityka API)
- **Skipped:** 56 (integracyjne/E2E)
- **Do dopasowania:** 51 (serwisy)
- **Coverage:** ~85% core functionality

### Breakdown według kategorii

| Kategoria | Testy | Status | Opis |
|-----------|-------|--------|------|
| **Critical paths** | 21 | ✅ 100% | Najważniejsze ścieżki biznesowe |
| **Core services** | 24 | ✅ 100% | PersonaGenerator, Memory, Summarizer |
| **Security & Auth** | 36 | ✅ 100% | Hasła, JWT, walidacja |
| **API basics** | 10 | ✅ 100% | Root, health, validation |
| **Analityka & Graph API** | 17 | ✅ 100% | Generowanie insightów i grafów |
| **Models** | 26 | ⚠️ 70% | DB models (niektóre failują) |
| **Services** | 45 | 🔧 0% | Focus groups, graph, survey |
| **E2E** | 20 | 📋 Docs | Pełne scenariusze (skipped) |

### Co zostało przetestowane (✅ 100%)

#### 1. **Krytyczne ścieżki biznesowe** (test_critical_paths.py)
- ✅ Rozkłady demograficzne sumują się do 1.0
- ✅ Big Five traits w zakresie [0, 1]
- ✅ Chi-square validation odrzuca złe rozkłady
- ✅ Metryki wydajności (<30s total, <3s per persona)
- ✅ Event sourcing (sequence numbers, embeddings)
- ✅ Security (hasła hashowane, JWT expiration)
- ✅ DB constraints (foreign keys, required fields)
- ✅ Error handling (division by 0, None checks)

#### 2. **Security & Authentication**
- ✅ Hashowanie haseł (bcrypt)
- ✅ JWT tokens z expiration
- ✅ Walidacja słabych haseł
- ✅ Szyfrowanie API keys
- ✅ Email normalizacja
- ✅ SQL injection protection

#### 3. **Generowanie person**
- ✅ Weighted sampling z rozkładów
- ✅ Big Five personality traits
- ✅ Hofstede cultural dimensions
- ✅ Chi-square statistical validation
- ✅ Diversity scoring

#### 4. **Event sourcing & Memory**
- ✅ Generowanie embeddings
- ✅ Formatowanie kontekstu
- ✅ Cosine similarity
- ✅ Event ordering (sequence numbers)

#### 5. **Analityka i Graph API** (`test_analysis_api.py`, `test_graph_analysis_api.py`)
- ✅ Generowanie insightów z pełną obsługą błędów (404 dla brakujących danych, 500 dla błędów serwera)
- ✅ Wykorzystanie cache (pobieranie zapisanych podsumowań bez ponownego liczenia)
- ✅ Grupowanie transkryptów odpowiedzi po pytaniach z zachowaniem kolejności
- ✅ Budowa grafu i wszystkie widoki analityczne (kluczowe persony, koncepty, kontrowersje, korelacje cech, emocje)
- ✅ Obsługa zapytań w języku naturalnym do grafu wraz z zamykaniem połączeń z serwisem
- ✅ Mapowanie wyjątków `ValueError`/`ConnectionError` na odpowiednio 400/503 oraz wymuszenie nagłówka autoryzacyjnego

### 🔍 Co jeszcze warto przetestować
- 🔒 Scenariusze autoryzacji/uwierzytelnienia dla użytkowników bez dostępu do danej grupy fokusowej (obecnie testujemy tylko brak tokena)
- ♻️ Inwalidacja cache po ponownym wygenerowaniu insightów oraz konkurencyjne wywołania POST/GET
- ⚙️ Parametry zapytań (np. `include_recommendations=False`, różne `filter_type` dla grafu) i walidacja payloadów zapytań `ask`
- 🚨 Mapowanie niespodziewanych wyjątków GraphService na `500` oraz logowanie (przetestować ścieżkę `Exception`)
- 📊 Integracja z realną bazą danych w celu zweryfikowania, że struktura odpowiedzi zgadza się z modelami (testy integracyjne, gdy środowisko będzie gotowe)

---

## 🎯 Uruchamianie testów

### Podstawowe komendy

```bash
# Wszystkie testy jednostkowe (95 testów przechodzi)
python -m pytest tests/ -v

# Z krótszym output
python -m pytest tests/ -v --tb=short

# Tylko failures
python -m pytest tests/ -v --tb=short -x  # stop at first failure

# Show print statements
python -m pytest tests/ -v -s

# Konkretny plik
python -m pytest tests/test_critical_paths.py -v

# Konkretny test
python -m pytest tests/test_critical_paths.py::TestPersonaGenerationCriticalPath::test_big_five_traits_in_valid_range -v

# Pattern matching
python -m pytest tests/ -v -k "password"  # wszystkie testy z "password" w nazwie
python -m pytest tests/ -v -k "not slow"  # exclude slow tests
```

### Coverage reports

```bash
# HTML report (otwórz htmlcov/index.html)
python -m pytest tests/ --cov=app --cov-report=html

# Terminal report
python -m pytest tests/ --cov=app --cov-report=term

# XML (dla CI/CD)
python -m pytest tests/ --cov=app --cov-report=xml

# Tylko missing lines
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### Filtrowanie według markers

```bash
# Tylko unit tests
python -m pytest tests/ -v -m "not integration and not e2e"

# Tylko integration tests
python -m pytest tests/ -v -m integration

# Tylko slow tests
python -m pytest tests/ -v -m slow

# Skip slow tests
python -m pytest tests/ -v -m "not slow"
```

### Parallel execution (szybciej)

```bash
# Install plugin
pip install pytest-xdist

# Run in parallel (auto-detect CPUs)
python -m pytest tests/ -n auto

# Specific number of workers
python -m pytest tests/ -n 4
```

### Watch mode (re-run on changes)

```bash
# Install plugin
pip install pytest-watch

# Auto-rerun on file changes
ptw tests/
```

---

## 🔧 Testy wymagające środowiska

### Problem: Testy serwisów (focus_group, graph, survey)

Te testy wywołują **prywatne metody** (`_method_name()`) które nie są bezpośrednio dostępne.

#### ❌ Przykład problemu:
```python
# test_focus_group_service.py
async def test_load_personas(service, mock_db):
    # Ta metoda jest prywatna (_load_personas)
    personas = await service._load_personas(mock_db, persona_ids)
    # AttributeError: '_load_personas' is not accessible
```

#### ✅ Rozwiązania:

**Opcja 1: Testuj tylko publiczne API**
```python
@pytest.mark.asyncio
async def test_run_focus_group_integration(db_session):
    """Test całego flow przez publiczny run_focus_group()"""
    from app.services.focus_group_service_langchain import FocusGroupServiceLangChain

    service = FocusGroupServiceLangChain()

    # Mock persony i focus group w bazie
    # ...

    result = await service.run_focus_group(db_session, focus_group_id)

    assert result["status"] == "completed"
    assert len(result["responses"]) > 0
```

**Opcja 2: Dodaj test wrappers (dla development)**
```python
# W app/services/focus_group_service_langchain.py
from app.core.config import get_settings

class FocusGroupServiceLangChain:
    # ... existing methods ...

    # Dodaj sekcję dla testów
    if get_settings().ENVIRONMENT in ["development", "test"]:
        async def test_load_personas(self, db, persona_ids):
            """Wrapper for testing private method"""
            return await self._load_personas(db, persona_ids)

        def test_create_prompt(self, persona, question, context, description):
            """Wrapper for testing private method"""
            return self._create_persona_prompt(persona, question, context, description)
```

**Opcja 3: Użyj mocków dla pełnych testów**
```python
@pytest.mark.asyncio
async def test_focus_group_flow_with_mocks():
    """Test z mockami LLM i DB"""
    from unittest.mock import AsyncMock, MagicMock

    # Mock all dependencies
    mock_db = AsyncMock()
    mock_llm = AsyncMock()

    service = FocusGroupServiceLangChain()
    service.llm = mock_llm

    # Test flow
    # ...
```

### Setup: Testy integracyjne (wymagają DB)

#### 1. Przygotuj testową bazę danych

**Opcja A: Docker Compose**
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: test_market_research_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user"]
      interval: 5s
      timeout: 5s
      retries: 5

  test-redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"

  test-neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/testpass
    ports:
      - "7475:7474"
      - "7688:7687"
```

Start:
```bash
docker-compose -f docker-compose.test.yml up -d
```

**Opcja B: Użyj istniejącej bazy**
```bash
# Utwórz testową bazę
psql -U postgres -c "CREATE DATABASE test_market_research_db;"
```

#### 2. Setup zmiennych środowiskowych

```bash
# .env.test (utwórz ten plik)
DATABASE_URL=postgresql+asyncpg://test_user:test_pass@localhost:5433/test_market_research_db
REDIS_URL=redis://localhost:6380
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=testpass
GOOGLE_API_KEY=your_gemini_api_key_here
ENVIRONMENT=test
```

Load env:
```bash
export $(cat .env.test | xargs)
```

#### 3. Zastosuj migracje

```bash
# Z Docker
docker-compose -f docker-compose.test.yml exec test-postgres bash
alembic upgrade head

# Lub lokalnie
export DATABASE_URL="postgresql+asyncpg://test_user:test_pass@localhost:5433/test_market_research_db"
alembic upgrade head
```

#### 4. Uruchom testy integracyjne

```bash
# Wszystkie testy (włącznie z integration)
python -m pytest tests/ -v --no-skip

# Tylko integration
python -m pytest tests/ -v -m integration

# Tylko models
python -m pytest tests/test_models.py -v
```

#### 5. Cleanup

```bash
# Stop i usuń kontenery
docker-compose -f docker-compose.test.yml down -v

# Lub drop database
psql -U postgres -c "DROP DATABASE test_market_research_db;"
```

### Setup: Testy E2E (pełne środowisko)

Testy E2E wymagają:
- ✅ PostgreSQL (database)
- ✅ Redis (cache)
- ✅ Neo4j (graph)
- ✅ Gemini API key (LLM)

```bash
# 1. Start wszystkich serwisów
docker-compose up -d

# 2. Zastosuj migracje
docker-compose exec api alembic upgrade head

# 3. Export API key
export GOOGLE_API_KEY="your_real_gemini_key"

# 4. Uruchom E2E tests
python -m pytest tests/test_e2e_integration.py::TestCompleteResearchFlow::test_full_research_workflow --no-skip -v

# 5. Cleanup
docker-compose down
```

---

## 🎁 Fixtures (conftest)

Plik `conftest.py` zawiera fixtures używane przez testy.

### Database fixtures

```python
# Użycie w teście
@pytest.mark.asyncio
async def test_create_project(db_session):
    """Test z prawdziwą bazą danych"""
    from app.models.project import Project

    project = Project(
        id=uuid4(),
        owner_id=uuid4(),
        name="Test",
        target_demographics={},
        target_sample_size=10
    )

    db_session.add(project)
    await db_session.commit()

    assert project.id is not None
```

### Mock fixtures

```python
# Mock LLM (bez wywoływania Gemini API)
def test_generate_response(mock_llm):
    """Test z mock LLM"""
    service = MyService()
    service.llm = mock_llm

    # mock_llm zwróci predefiniowaną odpowiedź
    response = await service.generate_something()
    assert "mocked" in response
```

### API fixtures

```python
def test_endpoint(api_client):
    """Test endpointu API"""
    response = api_client.get("/api/v1/projects")
    assert response.status_code == 200

def test_protected_endpoint(api_client, auth_headers):
    """Test z autentykacją"""
    response = api_client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
```

### Sample data fixtures

```python
def test_persona_creation(sample_persona_dict):
    """Test z przykładowymi danymi"""
    from app.models.persona import Persona

    persona = Persona(**sample_persona_dict)
    assert persona.age == 30
    assert persona.gender == "female"
```

### Dostępne fixtures:

| Fixture | Opis | Wymaga |
|---------|------|--------|
| `db_session` | Sesja DB z rollbackiem | Test DB |
| `test_engine` | Engine testowej DB | Test DB |
| `mock_llm` | Mock Gemini API | - |
| `mock_settings` | Mock konfiguracji | - |
| `api_client` | FastAPI TestClient | - |
| `auth_headers` | Headers z JWT | - |
| `sample_persona_dict` | Przykładowa persona | - |
| `sample_project_dict` | Przykładowy projekt | - |
| `temp_file` | Tymczasowy plik | - |

---

## ➕ Dodawanie nowych testów

### Szablon testu jednostkowego

```python
"""Testy dla ModuleService."""

import pytest
from app.services.module_service import ModuleService


@pytest.fixture
def service():
    """Fixture - instancja serwisu."""
    return ModuleService()


def test_feature_basic_case(service):
    """Test podstawowego przypadku użycia."""
    result = service.feature("input")
    assert result == "expected_output"


def test_feature_edge_case(service):
    """Test przypadku brzegowego."""
    result = service.feature("")
    assert result is None


def test_feature_error_handling(service):
    """Test obsługi błędu."""
    with pytest.raises(ValueError, match="Invalid input"):
        service.feature(None)


@pytest.mark.asyncio
async def test_async_feature(service):
    """Test metody asynchronicznej."""
    result = await service.async_feature()
    assert isinstance(result, dict)
    assert "status" in result
```

### Szablon testu integracyjnego

```python
"""Testy integracyjne API."""

import pytest
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_project_integration(db_session):
    """Test utworzenia projektu z prawdziwą bazą."""
    from app.models.project import Project

    project = Project(
        id=uuid4(),
        owner_id=uuid4(),
        name="Integration Test",
        target_demographics={"age_group": {"25-34": 1.0}},
        target_sample_size=10
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    assert project.id is not None
    assert project.name == "Integration Test"
```

### Szablon testu E2E

```python
"""Test pełnego scenariusza."""

import pytest


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_research_workflow(api_client, auth_headers):
    """
    Test pełnego workflow badania:
    1. Create project
    2. Generate personas
    3. Create focus group
    4. Run focus group
    5. Get results
    """
    # Step 1: Create project
    project_data = {
        "name": "E2E Test Project",
        "target_demographics": {
            "age_group": {"25-34": 0.5, "35-44": 0.5}
        },
        "target_sample_size": 10
    }

    response = api_client.post(
        "/api/v1/projects",
        json=project_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    project_id = response.json()["id"]

    # Step 2: Generate personas
    response = api_client.post(
        f"/api/v1/projects/{project_id}/personas/generate",
        json={"num_personas": 10},
        headers=auth_headers
    )
    assert response.status_code == 200

    # ... more steps
```

### Best practices

1. **Nazewnictwo**: `test_<feature>_<scenario>`
2. **Jeden test = jedna asercja** (lub grupa related asserts)
3. **Arrange-Act-Assert** pattern:
   ```python
   def test_something():
       # Arrange - setup
       service = MyService()
       data = {"key": "value"}

       # Act - wykonaj akcję
       result = service.process(data)

       # Assert - sprawdź wynik
       assert result["status"] == "success"
   ```
4. **Fixtures dla shared setup**
5. **Mocki dla zewnętrznych zależności**
6. **Docstringi wyjaśniające CO i DLACZEGO**

---

## 🔄 CI/CD (GitHub Actions)

### Przykładowa konfiguracja

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache pip
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov email-validator

      - name: Run unit tests
        run: |
          python -m pytest tests/ -v --tb=short --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run migrations
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
        run: |
          alembic upgrade head

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          python -m pytest tests/ -v -m integration --no-skip
```

### Pre-commit hook

```bash
# .git/hooks/pre-commit (utwórz ten plik)
#!/bin/bash
echo "Running tests before commit..."
python -m pytest tests/ -v --tb=short -x
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

Zrób executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 🐛 Debugging

### Verbose output
```bash
# Więcej info o failures
python -m pytest tests/ -vv --tb=long

# Pokaż wszystkie asserts (nawet passing)
python -m pytest tests/ -vv --tb=long -vv
```

### Pojedynczy test z debuggerem
```python
def test_something():
    import pdb; pdb.set_trace()  # Breakpoint
    result = my_function()
    assert result == expected
```

```bash
python -m pytest tests/test_file.py::test_something -s
```

### Show print statements
```bash
# -s = no capture (pokazuje print())
python -m pytest tests/ -v -s
```

### Show warnings
```bash
python -m pytest tests/ -v -W default
```

### Reruns on failure
```bash
pip install pytest-rerunfailures

# Retry failed tests 3 times
python -m pytest tests/ -v --reruns 3 --reruns-delay 1
```

### Profiling (slow tests)
```bash
pip install pytest-profiling

python -m pytest tests/ --profile
```

### HTML report
```bash
pip install pytest-html

python -m pytest tests/ --html=report.html --self-contained-html
```

---

## ❓ FAQ

### Q: Dlaczego niektóre testy są skipped?
**A:** Wymagają pełnego środowiska (DB, Neo4j, Gemini API). Służą jako dokumentacja oczekiwanych scenariuszy. Zobacz sekcję "Testy wymagające środowiska".

### Q: Jak uruchomić WSZYSTKIE testy jedną komendą?
**A:**
```bash
# Tylko jednostkowe (działają bez setup)
python -m pytest tests/ -v

# Z integracją (wymaga DB)
export DATABASE_URL="postgresql+asyncpg://..."
python -m pytest tests/ -v --no-skip
```

### Q: Jak uruchomić testy focus_group_service?
**A:** Obecnie wymagają dopasowania - testują prywatne metody. Zobacz sekcję "Testy wymagające środowiska" → "Opcja 1: Testuj tylko publiczne API".

### Q: Czy potrzebuję prawdziwego Gemini API key?
**A:**
- **NIE** dla unit testów (używamy mocków)
- **TAK** dla testów E2E i rzeczywistej integracji

### Q: Testy są wolne, jak przyspieszyć?
**A:**
```bash
# Parallel execution
pip install pytest-xdist
python -m pytest tests/ -n auto

# Tylko szybkie testy
python -m pytest tests/ -v -m "not slow"
```

### Q: Jak dodać nowy test?
**A:** Zobacz sekcję "Dodawanie nowych testów" - masz tam gotowe szablony.

### Q: Co to jest conftest.py?
**A:** Plik z fixtures (współdzielonymi setupami). Zobacz sekcję "Fixtures".

### Q: Jak testować prywatne metody?
**A:** Opcje:
1. Testuj przez publiczne API
2. Dodaj test wrappers (tylko dla dev/test)
3. Użyj mocków dla całego flow

### Q: Jak zrobić coverage report?
**A:**
```bash
python -m pytest tests/ --cov=app --cov-report=html
# Otwórz htmlcov/index.html w przeglądarce
```

### Q: Testy failują lokalnie ale działają w CI?
**A:** Sprawdź:
- Wersje dependencies (`pip freeze`)
- Zmienne środowiskowe
- Różnice w DB (local vs CI)
- Cache (`pytest --cache-clear`)

### Q: Jak testować async functions?
**A:**
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result is not None
```

---

## 📈 Metryki sukcesu

### Obecne
- ✅ 95 testów przechodzi (100% unit tests)
- ✅ 202 testy total
- ✅ ~85% coverage core functionality
- ✅ 21 critical path tests
- ✅ 0 bezpieczeństwa issues

### Cele
- [ ] 90%+ coverage
- [ ] Wszystkie 202 testy przechodzą
- [ ] <5s execution time (unit tests)
- [ ] CI/CD integration
- [ ] 10+ E2E scenarios

---

## 🎯 Priorytetowe akcje

### Teraz (Priorytet 1)
```bash
# Uruchom wszystkie działające testy
python -m pytest tests/ -v

# Sprawdź coverage
python -m pytest tests/ --cov=app --cov-report=html
```

### Niedługo (Priorytet 2)
- Fix failujące testy w test_models.py
- Dopasuj testy serwisów (focus_group, graph, survey)
- Setup test database dla integration tests

### Przyszłość (Priorytet 3)
- CI/CD integration
- 10+ E2E scenarios
- Performance testing
- Load testing