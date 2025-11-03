# Dokumentacja QA i Testowania - Sight Platform

**Wersja:** 2.3 | **Ostatnia aktualizacja:** 2025-11-03

System testów dla platformy Sight został zaprojektowany jako kompleksowy mechanizm zapewnienia jakości oprogramowania, łącząc testy jednostkowe, integracyjne, end-to-end, wydajnościowe oraz obsługi błędów w spójny ekosystem. Nasz cel to nie tylko weryfikacja poprawności funkcjonalnej, ale również budowanie zaufania poprzez dokładne pokrycie scenariuszy użycia, weryfikację wydajności oraz zapewnienie odporności na błędy.

## Statystyki Globalne

**Aktualna suite testów (wersja 2.3):**

- **Łączna liczba testów:** 444 funkcje testowe
- **Pliki testowe:** 66 plików w 5 kategoriach
- **Pokrycie kodu:** ~87% overall, ~92% dla krytycznych serwisów
- **Testy pomijane:** 5 (1.1% - kontrolowane przypadki brzegowe)
- **Czas wykonania:**
  - Testy szybkie (bez `@pytest.mark.slow`): ~90s
  - Pełna suita z LLM: 5-10 minut

**Trend wzrostu:**
- Październik 2024: ~380 testów, 85% pokrycia
- Listopad 2025: 444 testy, 87% pokrycia
- Wzrost: +17% liczby testów, +2% pokrycia w ciągu roku

## Piramida Testów

Nasza strategia testowania opiera się na klasycznej piramidzie testów z dodatkowymi warstwami dla wydajności i obsługi błędów:

```
                    ┌──────────────┐
                    │  E2E (12)    │  2.7% - Pełne scenariusze użytkownika (2-5 min)
                    └──────────────┘
                  ┌──────────────────┐
                  │ Integration (63) │  14% - API + DB + External services (10-30s)
                  └──────────────────┘
              ┌────────────────────────┐
              │  Performance (5)       │  1.1% - Benchmarks, SLA compliance (5-10 min)
              └────────────────────────┘
          ┌──────────────────────────────┐
          │  Error Handling (9)          │  2% - Edge cases & failures (5-10s)
          └──────────────────────────────┘
    ┌────────────────────────────────────────┐
    │         Unit Tests (355)               │  80% - Isolated logic (<90s)
    └────────────────────────────────────────┘
```

**Uzasadnienie dystrybucji:**

**80% Unit Tests (355)** - Szybki feedback loop (<90s), deterministyczne wyniki bez zewnętrznych zależności, łatwe debugowanie z izolacją błędów, pokrycie logiki biznesowej i transformacji danych. Najniższy koszt utrzymania i najwyższa wartość diagnostyczna.

**14% Integration Tests (63)** - Weryfikacja współpracy komponentów, testy API z prawdziwą bazą danych, integracja LangChain + Gemini (z mockami). Balance między realistycznością a prędkością, wykrywanie problemów na poziomie integracji modułów.

**2.7% E2E Tests (12)** - Wysoki koszt czasowy (2-5 min), wymaga zewnętrznych serwisów (Gemini API). Focus na krytycznych user flows, smoke tests dla CI/CD, weryfikacja pełnych scenariuszy biznesowych.

**3.1% Performance + Error Handling (14)** - Niche scenarios wymagające specjalnego setupu, performance benchmarks przeciw SLA, edge cases i failure scenarios, weryfikacja odporności systemu.

## Kategorie Testów

### 1. Testy Jednostkowe (Unit Tests)

**Statystyki:** 355 testów (80% suite), czas wykonania <90s, cel: izolowana weryfikacja logiki serwisów

**Zakres pokrycia:**
- **Logika generacji person:** Sampling demograficzny, Big Five traits, psychografia
- **Serwisy RAG:** Hybrid search, graph transformations, document processing
- **Walidatory:** Chi-kwadrat, segment brief validation, demographic constraints
- **Modele ORM:** Relacje, constraints, cascade deletes
- **Utilities:** Language detection, datetime handling, Polish NLP

**Przykładowe testy krytyczne:**
- `test_demographic_distribution_sums_to_one` - Weryfikacja poprawności matematycznej rozkładów
- `test_big_five_traits_in_valid_range` - Sprawdzenie zakresów cech osobowości [0,1]
- `test_persona_must_have_required_fields` - Kompletność struktury danych persony
- `test_polish_character_handling` - Obsługa polskich znaków (ą, ć, ę, ł, ń, ó, ś, ź, ż)

**Kluczowe pliki:** `tests/unit/test_persona_generator.py`, `test_persona_orchestration.py`, `test_focus_group_service.py`, `test_rag_hybrid_search_service.py`, `test_rag_graph_service.py`, `test_survey_response_generator.py`, `test_critical_paths.py`, `test_models.py`, `test_language_detection.py`

### 2. Testy Integracyjne (Integration Tests)

**Statystyki:** 63 testy (14% suite), czas wykonania 10-30s, cel: weryfikacja współpracy komponentów

**Zakres pokrycia:**
- **API endpoints + baza danych:** CRUD operations, data persistence
- **Autentykacja JWT + autoryzacja:** Token validation, permission checks
- **CRUD projektów i person:** Lifecycle management
- **Integracja LangChain z Gemini API:** Z mockami dla szybkości
- **Focus groups orchestration:** Pełny workflow dyskusji
- **Dashboard analytics:** Agregacje danych, usage tracking

**Markery:** `@pytest.mark.integration` (wymaga DB session), `@pytest.mark.external` (wymaga Gemini API key, opcjonalne)

**Kluczowe testy:**
- `test_generate_personas_success` - E2E generacja person z API
- `test_focus_groups_api_integration` - Pełny flow grupy fokusowej
- `test_dashboard_orchestrator_pl_integration` - Dashboard analytics z polskimi danymi
- `test_auth_api_integration` - JWT authentication flow
- `test_projects_api_integration` - Project lifecycle management

**Kluczowe pliki:** `tests/integration/test_personas_api_integration.py`, `test_focus_groups_api_integration.py`, `test_surveys_api_integration.py`, `test_dashboard_api.py`, `test_auth_api_integration.py`, `test_projects_api_integration.py`

### 3. Testy End-to-End (E2E Tests)

**Statystyki:** 12 testów (2.7% suite), czas wykonania 2-5 minut, cel: weryfikacja pełnych scenariuszy użytkownika

**Zakres pokrycia:**
- **Rejestracja → Projekt → Generacja person → Focus group → Insights**
- **Survey workflow:** Utworzenie → distribucja → analiza odpowiedzi
- **CI smoke tests:** Weryfikacja podstawowej funkcjonalności
- **Multi-user scenarios:** Współdzielenie projektów, permissions

**Kluczowy scenariusz:**
```python
def test_complete_research_workflow_end_to_end():
    """
    Pełny flow:
    1. Rejestracja użytkownika (<1s)
    2. Utworzenie projektu (<1s)
    3. Generowanie 10 person (15-30s)
    4. Utworzenie focus group (<1s)
    5. Uruchomienie dyskusji 5 person × 3 pytania (30-60s)
    6. Budowa grafu wiedzy (10-20s)
    7. Generowanie insights (5-10s)

    Oczekiwany czas: 90-180 sekund
    """
```

**Markery:** `@pytest.mark.e2e` (testy end-to-end), `@pytest.mark.slow` (testy >10s), `@pytest.mark.external` (wymagają Gemini API)

**Kluczowe pliki:** `tests/e2e/test_e2e_full_workflow.py`, `test_e2e_survey_workflow.py`, `test_e2e_ci_smoke.py`, `test_orchestration_smoke.py`

### 4. Testy Wydajnościowe (Performance Tests)

**Statystyki:** 5 testów (1.1% suite), czas wykonania 5-10 minut, cel: weryfikacja spełnienia celów wydajnościowych (SLA)

**Cele wydajnościowe:**
- **Generowanie 20 person:** target <60s, ideal 30-45s
- **Focus group 20×4:** target <3 min, ideal <2 min
- **Survey 10×10:** target <60s
- **RAG hybrid search:** target <350ms
- **API response time:** target <500ms (P90)
- **DB query time:** target <100ms (P95)

**Markery:** `@pytest.mark.performance` (benchmark tests), `@pytest.mark.slow` (long-running tests)

**Kluczowy plik:** `tests/performance/test_performance.py`

### 5. Testy Obsługi Błędów (Error Handling Tests)

**Statystyki:** 9 testów (2% suite), czas wykonania 5-10s, cel: weryfikacja resilience i error recovery

**Zakres pokrycia:**
- **Timeout Gemini API → 503 Service Unavailable**
- **Quota exceeded → 429 Too Many Requests + retry logic**
- **Neo4j connection failures → graceful degradation**
- **Malformed LLM responses → JSON parsing errors**
- **Race conditions w generacji person**
- **Invalid demographic constraints**
- **Database connection pool exhaustion**

**Marker:** `@pytest.mark.error_handling`

**Kluczowy plik:** `tests/error_handling/test_error_handling.py`

## Organizacja Testów

### Struktura Katalogów

```
tests/
├── conftest.py                    # Plugin orchestration
├── fixtures/                      # Modular test fixtures (16 fixtures w 8 modułach)
│   ├── api.py                    # API client fixtures
│   ├── asyncio_loop.py           # Event loop fixtures
│   ├── config.py                 # Configuration mocks
│   ├── database.py               # DB session fixtures
│   ├── mocks.py                  # LLM + service mocks
│   ├── rag.py                    # RAG service mocks
│   ├── samples.py                # Sample data (personas, projects)
│   └── utils.py                  # Test utilities
├── unit/                          # 355 unit tests (<90s)
├── integration/                   # 63 integration tests (10-30s)
├── e2e/                           # 12 E2E tests (2-5 min)
├── performance/                   # 5 performance tests (5-10 min)
└── error_handling/                # 9 error handling tests (5-10s)
```

### Konwencje Nazewnictwa

**Pliki testowe:** `test_*.py` lub `*_test.py` - prefiks/sufiks `test_` wymagany przez pytest, nazwy opisowe odzwierciedlające testowany moduł.

**Funkcje testowe:**
```python
# Unit tests
def test_demographic_distribution_sums_to_one():
    """KRYTYCZNE: Rozkłady demograficzne muszą sumować się do 1.0."""
    ...

# Async tests
@pytest.mark.asyncio
async def test_generate_personas_success(db_session):
    """Test pomyślnego wygenerowania person z API."""
    ...

# Parametrized tests
@pytest.mark.parametrize("age,gender,expected", [
    (25, "male", "young-male"),
    (45, "female", "middle-aged-female"),
])
def test_segment_classification(age, gender, expected):
    ...
```

### Markery Testów

System markerów pozwala na selektywne uruchamianie testów:

```python
# Kategorie testów
@pytest.mark.integration   # Wymaga DB session
@pytest.mark.e2e          # End-to-end workflow
@pytest.mark.performance  # Performance benchmark

# Charakterystyki
@pytest.mark.slow         # Testy >10s
@pytest.mark.external     # Wymaga Gemini API key

# Kontrola wykonania
@pytest.mark.skipif       # Warunkowe pomijanie
@pytest.mark.xfail        # Expected failures

# Parametryzacja
@pytest.mark.parametrize  # Data-driven tests
```

**Użycie:**
```bash
pytest -v -m "not slow"                    # Tylko szybkie testy
pytest -v -m integration                   # Tylko testy integracyjne
pytest -v -m external                      # Testy wymagające Gemini API
pytest -v -m performance                   # Performance benchmarks
pytest -v -m "integration and not external" # Kombinacje markerów
```

## Kluczowe Fixtury Testowe

System fixtures wykorzystuje modularną architekturę (16 głównych fixtures w 8 modułach) eliminującą powtarzalny kod i przyspieszającą pisanie testów.

### 1. Database Fixtures (`tests/fixtures/database.py`)

```python
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Izolowany async SQLAlchemy engine przeciw test_sight_db."""

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Transakcyjna AsyncSession z automatycznym rollbackiem po teście."""
```

**Użycie:** Każdy test otrzymuje świeżą sesję z automatycznym rollbackiem.

### 2. API Fixtures (`tests/fixtures/api.py`)

```python
@pytest.fixture
def api_client() -> TestClient:
    """FastAPI TestClient bez exception bubbling."""

@pytest.fixture
def auth_headers() -> dict[str, str]:
    """One-off JWT header dla authenticated requests."""

@pytest_asyncio.fixture
async def authenticated_client(db_session):
    """Zwraca: (TestClient, User, headers) - persisted user w DB, ważny JWT token, gotowe headers."""

@pytest_asyncio.fixture
async def project_with_personas(db_session, authenticated_client):
    """Zwraca: (Project, List[Persona], TestClient, headers) - projekt z 10 deterministycznymi personami."""

@pytest_asyncio.fixture
async def completed_focus_group(db_session, project_with_personas):
    """Zwraca: (FocusGroup, List[PersonaResponse], TestClient, headers) - ukończona grupa fokusowa z odpowiedziami."""
```

### 3. Mock Fixtures (`tests/fixtures/mocks.py`)

```python
@pytest.fixture
def mock_settings():
    """Deterministyczne ustawienia konfiguracji."""

@pytest.fixture
def mock_llm():
    """AsyncMock dla LangChain LLM interface."""

@pytest.fixture
def mock_datetime():
    """Freezing datetime.now() dla deterministycznych testów."""
```

### 4. RAG Fixtures (`tests/fixtures/rag.py`)

```python
@pytest.fixture
def mock_neo4j_driver():
    """AsyncMock dla Neo4j AsyncDriver."""

@pytest.fixture
def mock_vector_store():
    """Mock Neo4j vector store dla hybrid search tests."""

@pytest.fixture
def mock_embeddings():
    """Deterministyczne embeddingi (768 wymiarów) oparte na hash(text)."""

@pytest.fixture
def mock_gemini_2_5_pro():
    """AsyncMock dla Gemini 2.5 Pro z realistycznym allocation plan."""
```

### 5. Sample Data Fixtures (`tests/fixtures/samples.py`)

```python
@pytest.fixture
def sample_persona_dict():
    """Minimalna struktura persony dla schema/unit tests."""

@pytest.fixture
def sample_project_dict():
    """Minimalna struktura projektu z target demographics."""
```

## Metryki Pokrycia

### Aktualny Stan Pokrycia

| Moduł | Cel | Aktualny | Gap | Status |
|-------|-----|----------|-----|--------|
| **app/services/** | 85%+ | ~87% | -2% | ✅ HIGH |
| app/services/personas/ | 90%+ | 92% | +2% | ✅ |
| app/services/focus_groups/ | 90%+ | 89% | -1% | ⚠️ |
| app/services/rag/ | 85%+ | 84% | -1% | ⚠️ |
| app/services/surveys/ | 85%+ | 81% | -4% | 🔴 |
| **app/api/** | 85%+ | ~88% | +3% | ✅ |
| **app/models/** | 95%+ | ~96% | +1% | ✅ |
| **app/core/** | 90%+ | ~93% | +3% | ✅ |
| **app/db/** | 90%+ | ~91% | +1% | ✅ |
| **Ogólnie** | 85%+ | ~87% | +2% | ✅ |

### Krytyczne Luki w Pokryciu

**🔴 app/services/surveys/survey_response_generator.py (81% - target: 85%+)**
- **Missing:** Error handling dla malformed questions, validation polskich znaków, edge case survey z 0 pytań, handling bardzo długich odpowiedzi (>2000 chars)
- **Effort:** 2 dni | **Owner:** Backend Engineer

**🔴 app/services/rag/rag_graph_service.py (84% - target: 85%+)**
- **Missing:** Neo4j connection failure scenarios, Cypher query injection prevention, graph transformation edge cases, performance test dla 1000+ nodes
- **Effort:** 3 dni | **Owner:** RAG Engineer

**⚠️ app/services/focus_groups/discussion_summarizer.py (89% - target: 90%+)**
- **Missing:** Summarization z długimi odpowiedziami (>2000 tokens), Polish sentiment analysis accuracy tests, multi-language mixing (PL/EN)
- **Effort:** 2 dni | **Owner:** NLP Engineer

**⚠️ Integration Tests dla Neo4j Graph Operations**
- **Status:** Brak testów integracyjnych dla pełnego flow RAG Graph
- **Gap:** Testy jednostkowe OK, brakuje weryfikacji z prawdziwym Neo4j
- **Effort:** 5 dni | **Owner:** Backend Engineer + QA

**Znane wykluczone obszary:** `app/main.py` (FastAPI startup/shutdown testowane przez E2E), `app/core/config.py` (statyczna konfiguracja validowana przez pytest-env), `scripts/` (narzędzia administracyjne - manual testing), `migrations/` (Alembic - testowane manualnie)

## Benchmarki Wydajnościowe

### Cele Wydajnościowe (SLA Targets)

| Operacja | Target | Idealny | Aktualny | Status |
|----------|--------|---------|----------|--------|
| **Generacja 20 person** | <60s | 30-45s | ~45s | ✅ GREEN |
| **Focus group 20×4** | <3 min | <2 min | ~2 min | ✅ GREEN |
| **Survey 10×10** | <60s | 30-45s | ~40s | ✅ GREEN |
| **RAG hybrid search** | <350ms | <200ms | ~280ms | ✅ GREEN |
| **API response (90%ile)** | <500ms | <300ms | ~380ms | ✅ GREEN |
| **DB query (95%ile)** | <100ms | <50ms | ~65ms | ✅ GREEN |

### Szczegóły Performance Tests

**1. Persona Generation Performance**

Test: `test_persona_generation_performance_20_personas` - TARGET <60s, IDEAL 30-45s

Komponenty: Orchestration (5-10s) + RAG queries (5-10s) + LLM calls 20x parallel (20-30s) + Validation chi-square (1-2s) + DB persistence batch insert (2-5s)

**Aktualne wyniki:** Mean: 45.2s, P50: 44.8s, P90: 52.3s, P99: 58.7s

**Bottlenecki:** Gemini API rate limiting (5 RPM bez quota increase), network latency do Google API (~150-200ms per request), JSON parsing dla złożonych allocation plans

**Optymalizacje:** Async/await parallel execution (20x faster niż sequential), caching segment briefs (Redis, 24h TTL), batch LLM requests gdzie możliwe

**2. Focus Group Performance**

Test: `test_focus_group_discussion_performance` - TARGET <3 min, IDEAL <2 min

Komponenty: Memory loading (5-10s) + LLM calls 80x parallel (60-90s) + Response persistence batch insert (5-10s) + Summarization (10-20s)

**Aktualne wyniki:** Mean: 118.4s, P50: 115.2s, P90: 135.8s, P99: 158.3s

**3. RAG Hybrid Search Performance**

Test: `test_rag_hybrid_search_latency` - TARGET <350ms, IDEAL <200ms

Komponenty: Vector search embedding + similarity (100-150ms) + Fulltext search Neo4j Lucene (50-80ms) + RRF fusion (20-40ms) + Graph enrichment optional (+50-100ms)

**Aktualne wyniki:** Mean: 278ms, P50: 265ms, P90: 315ms, P99: 358ms (⚠️ powyżej targetu)

**Optymalizacje planowane:** Neo4j index tuning (FULLTEXT → VECTOR hybrid index), embedding caching dla popularnych zapytań, connection pooling dla Neo4j driver

## Uruchamianie Testów

### Podstawowe Komendy

```bash
# Domyślny zestaw testów (szybkie)
pytest -v

# Wszystkie testy (włącznie z wolnymi)
pytest -v --run-slow

# Testy z raportem pokrycia
pytest -v --cov=app --cov-report=html

# Tylko testy jednostkowe (~90s)
pytest tests/unit -v

# Tylko testy integracyjne (10-30s)
pytest tests/integration -v

# Testy end-to-end (2-5 min)
pytest tests/e2e/ -v --run-slow --run-external -s

# Performance benchmarks (5-10 min)
pytest tests/performance/ -v --run-slow --run-external

# Tylko szybkie testy (bez markerów slow)
pytest -v -m "not slow"

# Testy wymagające Gemini API
pytest -v -m external --run-external

# Kombinacje markerów
pytest -v -m "integration and not external"
```

### Pokrycie Kodu

```bash
# Raport HTML (najlepszy dla eksploracji)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Raport terminal (szybki overview)
pytest --cov=app --cov-report=term

# Raport XML (dla CI/CD)
pytest --cov=app --cov-report=xml

# Fail build jeśli pokrycie <85%
pytest --cov=app --cov-fail-under=85

# Pokrycie tylko dla serwisów
pytest --cov=app/services --cov-report=term
```

## Integracja CI/CD

### Strategia CI/CD

**PR Workflow:**

**1. Fast Feedback (2-5 min):**
- Unit tests (355 testów, ~90s)
- Error handling tests (9 testów, ~10s)
- Linting (ruff check, ~5s)
- Coverage threshold check (85%+)

**2. Integration Tests (5-10 min):**
- API + DB tests (63 testy, ~30s)
- Mocked external services (bez Gemini API)
- Redis + Neo4j + PostgreSQL w Docker

**3. E2E Smoke Tests (opcjonalne, 5-10 min):**
- Tylko na main branch
- Wymaga Gemini API key w secrets
- Smoke tests: podstawowe user flows

**Nightly Builds:**
- Pełna suita testów (wszystkie 444 testy)
- Performance benchmarks
- External service integration (prawdziwy Gemini API)
- Coverage report + trends

### Coverage Tracking

```bash
# Lokalnie
pytest --cov=app --cov-report=html --cov-report=term

# CI/CD
pytest --cov=app --cov-report=xml --cov-fail-under=85
```

**Thresholdy:**
- Overall: 85% (fail build jeśli <85%)
- Services: 85% (warning jeśli <85%)
- Critical paths: 90% (fail build jeśli <90%)

**Codecov Integration (zalecane):**
- Automatyczne komentarze na PR z coverage diff
- Trend tracking (coverage over time)
- File-level coverage heatmaps

## Bramy Jakości (Quality Gates)

### Checklist Przed Deploymentem na Produkcję

**✅ Testy**
- [ ] **Wszystkie testy przechodzą:** `pytest -v` (444/444 ✅)
- [ ] **Pokrycie ≥85% overall:** `pytest --cov=app --cov-report=term`
- [ ] **Pokrycie ≥85% services:** `pytest --cov=app/services`
- [ ] **Pokrycie ≥90% critical paths:** `pytest tests/unit/test_critical_paths.py --cov`
- [ ] **Zero testów skipped (oprócz known xfails):** Max 5 skipped
- [ ] **Brak flaky tests:** 3x consecutive passes

**✅ Performance**
- [ ] **Generacja 20 person <60s:** `pytest -v -m performance -k persona_generation`
- [ ] **Focus group 20×4 <3min:** `pytest -v -m performance -k focus_group`
- [ ] **RAG hybrid search <350ms:** `pytest -v -m performance -k hybrid_search`
- [ ] **API response time <500ms (P90):** Load testing z Locust
- [ ] **DB query time <100ms (P95):** Monitoring z Datadog/New Relic

**✅ Code Quality**
- [ ] **Linting passes:** `ruff check app/` (zero errors)
- [ ] **No high-severity bugs:** SonarQube/CodeQL scan
- [ ] **No security vulnerabilities:** `pip-audit` + Snyk scan

**✅ Infrastructure**
- [ ] **Migracje zastosowane:** `alembic upgrade head`
- [ ] **Neo4j indeksy utworzone:** `python scripts/init_neo4j_indexes.py`
- [ ] **Redis działa:** `docker-compose up redis -d && redis-cli ping`

**✅ Configuration**
- [ ] **Zmienne środowiskowe ustawione:** SECRET_KEY, GOOGLE_API_KEY, DATABASE_URL, NEO4J_URI, REDIS_URL, ENVIRONMENT=production
- [ ] **Config validation passes:** `python scripts/config_validate.py`
- [ ] **No secrets in code/git history:** `git secrets --scan`

## Znany Dług Techniczny (Testing Focus)

### 🔴 Priorytet 1: Krytyczne Luki (Q1 2025)

**1. Brakujące E2E Testy dla Survey Workflows**
- **Status:** Częściowe pokrycie (1 E2E test, brak edge cases)
- **Impact:** HIGH - Survey functionality nie ma comprehensive E2E coverage
- **Gap:** Survey creation z validation errors, distribution do 50+ person (performance), response analysis + insights, export results (CSV, PDF)
- **Effort:** 3-5 dni | **Owner:** QA Engineer

**2. Integration Tests dla Neo4j Graph Operations**
- **Status:** Unit tests OK, brakuje integration tests z prawdziwym Neo4j
- **Impact:** HIGH - RAG Graph functionality nie ma weryfikacji z prawdziwą bazą
- **Gap:** Full graph ingestion workflow (documents → chunks → embeddings → Neo4j), Cypher query generation + execution (z prawdziwym LLM), graph traversal dla complex queries, performance testing dla 1000+ nodes
- **Effort:** 5-7 dni | **Owner:** Backend Engineer + QA

**3. Performance Tests dla 100+ Persona Generation**
- **Status:** Brak testów dla dużych projektów (max tested: 20 person)
- **Impact:** MEDIUM - Nie wiemy jak system się zachowa przy 100+ personach
- **Gap:** Generacja 100 person, memory consumption test (czy nie OOM), DB performance (batch inserts, indexy), LLM rate limiting handling (Gemini API quota)
- **Effort:** 2-3 dni | **Owner:** Performance Engineer

### ⚠️ Priorytet 2: Ważne Luki (Q2 2025)

**4. Security Tests (SQL Injection, XSS, Auth Bypass)**
- **Status:** Brak dedykowanych security tests
- **Impact:** MEDIUM - Potencjalne security vulnerabilities
- **Gap:** SQL injection prevention tests, XSS prevention tests, auth bypass tests (JWT validation), CSRF protection tests, rate limiting bypass tests
- **Effort:** 3-4 dni | **Owner:** Security Engineer + QA

**5. Load Tests dla Concurrent Users**
- **Status:** Brak load testów
- **Impact:** MEDIUM - Nie wiemy jak system się zachowa przy 10+ concurrent users
- **Gap:** 10 concurrent users generating personas, 5 concurrent focus groups, DB connection pooling stress test, Redis cache hit rate under load
- **Effort:** 2-3 dni | **Owner:** Performance Engineer | **Tools:** Locust, k6, Artillery

**6. Polish NLP Edge Cases**
- **Status:** Podstawowe testy OK, brakuje edge cases
- **Impact:** LOW - Edge cases dla polskich znaków specjalnych
- **Gap:** Polskie znaki w odpowiedziach, sentiment analysis accuracy dla polskich idiomów, language detection dla mixed PL/EN, tokenization dla długich słów (>30 znaków)
- **Effort:** 1-2 dni | **Owner:** NLP Engineer

## Rozwiązywanie Problemów

### Top 5 Typowych Problemów

**1. Brak połączenia z bazą danych**
- **Objawy:** Testy integracyjne failują z connection refused, `sqlalchemy.exc.OperationalError`
- **Rozwiązanie:**
  ```bash
  docker-compose ps                           # Sprawdź status
  docker-compose up -d postgres              # Uruchom bazę
  docker-compose exec postgres psql -U sight -d sight_db -c "SELECT 1"  # Zweryfikuj
  docker-compose logs postgres               # Sprawdź logi
  ```

**2. Problemy z Gemini API**
- **Objawy:** Testy external failują z 401 Unauthorized, `google.api_core.exceptions.Unauthenticated`
- **Rozwiązanie:**
  ```bash
  echo $GOOGLE_API_KEY                       # Zweryfikuj klucz
  # Sprawdź quota: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
  pytest -v -m "not external"                # Pomiń testy wymagające API
  ```

**3. Testy E2E nie uruchamiają się**
- **Objawy:** E2E tests są skipowane, `skipped: use --run-slow --run-external to run`
- **Rozwiązanie:**
  ```bash
  pytest tests/e2e/ -v --run-slow --run-external -s  # Użyj wymaganych flag
  # Lub ustaw zmienne środowiskowe:
  export RUN_SLOW_TESTS=1
  export RUN_EXTERNAL_TESTS=1
  pytest tests/e2e/ -v
  ```

**4. Flaky Tests (niestabilne testy)**
- **Objawy:** Testy czasami przechodzą, czasami failują, race conditions w testach async
- **Rozwiązanie:**
  ```bash
  pytest -v tests/integration/test_focus_groups_api.py --count=10  # Uruchom wielokrotnie
  pip install pytest-repeat
  pytest -v --count=10 tests/integration/     # Użyj pytest-repeat
  pytest -v -s tests/integration/test_focus_groups_api.py  # Debug z verbose
  ```

**5. Neo4j connection failures w testach**
- **Objawy:** `neo4j.exceptions.ServiceUnavailable: Could not connect to Neo4j`
- **Rozwiązanie:**
  ```bash
  docker-compose up -d neo4j                 # Uruchom Neo4j
  docker-compose exec neo4j cypher-shell -u neo4j -p testpassword "RETURN 1"  # Sprawdź
  python scripts/init_neo4j_indexes.py       # Zainicjuj indeksy
  ```

## Podsumowanie

### Silne Strony

✅ **Wysoka piramida testów:** 80% unit, 14% integration, 3% E2E - optymalna dystrybucja dla szybkiego feedback

✅ **Pokrycie >85%:** Overall 87%, services 87%, models 96% - przekraczamy cele jakości

✅ **Modularny system fixtures:** 16 fixtures w 8 modułach - eliminacja powtarzalnego kodu

✅ **Performance benchmarks:** Wszystkie SLA targets spełnione - system jest wydajny

✅ **Fast feedback:** Unit tests <90s - deweloperzy dostają szybką informację zwrotną

✅ **Comprehensive test categories:** Unit, integration, E2E, performance, error handling - pełne spektrum testowania

### Obszary do Poprawy

🔴 **E2E coverage:** Brak comprehensive survey workflow tests - potrzebne pełne testy end-to-end dla ankiet

🔴 **Integration tests:** Neo4j graph operations nie przetestowane z prawdziwą bazą - ryzyko dla RAG functionality

🔴 **Large scale tests:** Brak testów dla 100+ person - nie wiemy jak system się skaluje

⚠️ **Security tests:** Brak dedykowanych security tests (SQL injection, XSS) - potencjalne luki bezpieczeństwa

⚠️ **Load tests:** Brak testów dla concurrent users - nie wiemy jak system radzi sobie pod obciążeniem

⚠️ **Polish NLP edge cases:** Podstawowe testy OK, brakuje edge cases - ryzyko dla polskich znaków specjalnych

### Roadmap Q1-Q2 2025

**Q1 2025:**
1. Implementacja E2E testów dla survey workflows (🔴 Priority 1, 3-5 dni)
2. Integration tests dla Neo4j graph operations (🔴 Priority 1, 5-7 dni)
3. Performance tests dla 100+ persona generation (🔴 Priority 1, 2-3 dni)

**Q2 2025:**
4. Security test suite (⚠️ Priority 2, 3-4 dni)
5. Load testing z Locust (⚠️ Priority 2, 2-3 dni)
6. Polish NLP edge cases (⚠️ Priority 2, 1-2 dni)

### Metryki Sukcesu

**Krótkoterminowe (Q1 2025):**
- [ ] Pokrycie E2E dla survey workflows: 0% → 90%
- [ ] Integration tests dla Neo4j: 0 testów → 5+ testów
- [ ] Performance tests dla 100 person: brak → test passing <5min

**Średnioterminowe (Q2 2025):**
- [ ] Security test suite: 0 testów → 15+ testów
- [ ] Load tests: brak → 10 concurrent users tested
- [ ] Overall coverage: 87% → 90%

**Długoterminowe (H2 2025):**
- [ ] CI/CD fully automated z GitHub Actions
- [ ] Codecov integration z PR comments
- [ ] Nightly builds z full external test suite
- [ ] Visual regression tests dla kluczowych UI flows

---

**Ostatnia aktualizacja:** 2025-11-03 | **Wersja dokumentu:** 2.3 | **Odpowiedzialny:** QA Engineering Team
