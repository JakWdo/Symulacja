# CLAUDE.md

Instrukcje dla Claude Code podczas pracy z tym projektem.

## Przegląd Projektu

**Market Research SaaS** - Platforma do wirtualnych grup fokusowych z AI.

**Stack:**
- Backend: FastAPI, PostgreSQL + pgvector, Redis, Neo4j
- Frontend: React 18 + TypeScript, Vite, TanStack Query, Tailwind
- AI: Google Gemini 2.5 (Flash/Pro) via LangChain
- Infrastruktura: Docker + Docker Compose

## Quick Start

```bash
# Uruchom wszystkie serwisy (development)
docker-compose up -d

# Rebuild po zmianach w dependencies
docker-compose up --build -d

# Logi
docker-compose logs -f api

# Migracje bazy
docker-compose exec api alembic upgrade head

# Inicjalizacja Neo4j indexes (WYMAGANE dla RAG!)
python scripts/init_neo4j_indexes.py

# Testy
python -m pytest tests/ -v
```

**Endpoints:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Neo4j Browser: http://localhost:7474

## Dokumentacja

**Główne pliki:**
- **README.md** - User-facing docs, quick start
- **CLAUDE.md** - Ten plik (instrukcje dla Claude)
- **docs/README.md** - Indeks dokumentacji technicznej
- **docs/DEVOPS.md** - DevOps, Docker, CI/CD, monitoring (44KB)
- **docs/TESTING.md** - Test suite (380 testów, fixtures, performance)
- **docs/RAG.md** - System RAG (Hybrid Search + GraphRAG, 38KB)
- **docs/AI_ML.md** - AI/LLM system, persona generation (40KB)
- **docs/QUICKSTART.md** - Quick start guide
- **docs/TROUBLESHOOTING.md** - Rozwiązywanie problemów
- **PLAN.md** - Roadmap i 46 zadań strategicznych (TIER 0-3)

## Architektura

### Service Layer Pattern

```
API Endpoints (app/api/*.py) - validation, routing
    ↓
Service Layer (app/services/*.py) - business logic
    ↓
Models/DB (app/models/*.py) - data access
```

### Kluczowe Serwisy

- `PersonaGeneratorLangChain` - Generuje persony z RAG + statistical sampling
- `FocusGroupServiceLangChain` - Orkiestracja dyskusji (async parallelization)
- `MemoryServiceLangChain` - Event sourcing z semantic search
- `RAGDocumentService` - Zarządzanie dokumentami (ingest, CRUD)
- `GraphRAGService` - Graph RAG (Cypher queries, answer_question)
- `PolishSocietyRAG` - Hybrid search (vector + keyword + RRF fusion)
- `GraphService` - *(archived)* Analiza focus groups (Neo4j concepts/emotions)

### Archived Services

**app/services/archived/** - Legacy features nie używane w obecnej wersji:
- `graph_service.py` - Focus group graph analysis (concept/emotion extraction)
  - Zachowane dla historii, ale ukryte z frontend UI
  - Zobacz `app/services/archived/README.md` dla instrukcji przywrócenia

### Wzorce

**1. Async/Await** - Wszędzie dla I/O (LLM, DB, Redis, Neo4j)
**2. Event Sourcing** - Pamięć person (immutable events + embeddings)
**3. Hybrid Search** - Vector + keyword search z RRF fusion
**4. Parallel Processing** - asyncio.gather dla równoległych LLM calls

## Konfiguracja (.env)

```bash
# WYMAGANE
GOOGLE_API_KEY=your_gemini_api_key

# Database
DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Security (ZMIEŃ W PRODUKCJI!)
SECRET_KEY=change-me
ENVIRONMENT=development
DEBUG=true

# RAG
RAG_USE_HYBRID_SEARCH=True
RAG_VECTOR_WEIGHT=0.7
RAG_TOP_K=5
```

## Konwencje Kodu

### Backend (Python)
- **Async/await** - wszędzie dla I/O
- **Type hints** - wymagane dla wszystkich funkcji
- **Docstringi** - po polsku (istniejąca konwencja)
- **LangChain** - abstrakcje dla LLM operations

### Frontend (TypeScript)
- **React Query** - server state
- **Zustand** - UI state
- **Tailwind CSS** - styling

### Testy
- **pytest + pytest-asyncio**
- **Coverage target:** 80%+ overall, 85%+ dla services
- **Markery:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`

## Workflow Deweloperski

### Typowe Operacje

```bash
# 1. Zmiana kodu Python/TypeScript → hot reload (NIE rebuild)

# 2. Zmiana requirements.txt / package.json → rebuild
docker-compose up --build -d

# 3. Nowa migracja bazy
docker-compose exec api alembic revision --autogenerate -m "opis"
docker-compose exec api alembic upgrade head

# 4. Testowanie
python -m pytest tests/ -v                    # Wszystkie
python -m pytest tests/test_*.py -v           # Konkretny plik
python -m pytest tests/ -v -m "not slow"      # Bez slow tests
```

### Tworzenie Nowej Funkcjonalności

1. **Analiza** - Sprawdź istniejącą architekturę w docs/
2. **Service Layer** - Dodaj logikę w `app/services/`
3. **API Endpoint** - Dodaj endpoint w `app/api/`
4. **Schema** - Dodaj Pydantic schema w `app/schemas/`
5. **Testy** - Dodaj unit + integration tests
6. **Dokumentacja** - Aktualizuj PLAN.md

## Rozwiązywanie Problemów

```bash
# Backend nie startuje
docker-compose logs api
docker-compose restart api postgres

# Frontend nie startuje
docker-compose logs frontend
docker-compose restart frontend

# Błędy bazy
docker-compose ps  # Sprawdź health
docker-compose down -v && docker-compose up -d  # Nuklearna opcja (usuwa dane!)

# Neo4j nie działa
docker-compose logs neo4j
docker-compose restart neo4j
python scripts/init_neo4j_indexes.py  # Re-create indexes
```

## Zasady Deweloperskie (SIGHT-SPECIFIC)

### Production-Ready Code

**Enterprise-Grade:**
- ✅ SOLID principles (gdzie sensowne)
- ✅ Type safety (type hints wszędzie)
- ✅ Error handling (comprehensive + informacyjne messages)
- ✅ Security (input validation, sanitization, auth/authz)
- ✅ Performance (async/await, caching, parallelization)

**Dokumentacja:**
- ✅ Docstringi w stylu Google/NumPy (po polsku)
- ✅ Inline comments wyjaśniają "dlaczego", nie "co"
- ✅ Examples w docstringach dla public API
- ✅ Performance notes (Big-O) dla algorytmów

**Testowanie:**
- ✅ Unit tests (coverage >80%)
- ✅ Integration tests (współpraca komponentów)
- ✅ Edge cases + error scenarios

### Architecture Patterns

**1. Service Layer** - Endpoints cienkie, serwisy grube
**2. Async/Await** - Wszędzie dla I/O (LLM, DB, Redis, Neo4j)
**3. Event Sourcing** - Immutable events + embeddings dla pamięci
**4. Hybrid Search** - Vector + keyword + RRF fusion
**5. Parallel Processing** - asyncio.gather dla LLM calls
**6. Error Handling** - Domain exceptions → Service → API → Frontend

### Common Pitfalls

1. **N+1 Queries** - Używaj `selectinload()` dla relations
2. **Token Limits** - Truncate context inteligentnie (priorytetyzuj must-have)
3. **Memory Leaks** - Używaj `asyncio.TaskGroup` dla cleanup
4. **Race Conditions** - Redis locks dla concurrent writes
5. **Connection Exhaustion** - Connection pooling + retry logic
6. **Stale Data** - Invalidate React Query cache po mutations

## Production Checklist

**Pre-Deploy:**
- [ ] Wszystkie testy przechodzą (380 tests)
- [ ] Coverage >80%
- [ ] Migrations up-to-date
- [ ] Neo4j indexes utworzone
- [ ] Secrets rotated i bezpieczne (NIE w .env w repo!)
- [ ] CORS tylko prod domains
- [ ] Rate limiting włączony
- [ ] Health check działa
- [ ] Docker services running (postgres, redis, neo4j, api, frontend)

**Post-Deploy:**
- [ ] Smoke tests (login, personas, focus group)
- [ ] Performance checks (API <500ms, persona <5s)
- [ ] Monitoring (error rate <1%, CPU <70%, memory stable)

## PLAN.md - Zarządzanie Zadaniami

**WAŻNE:** Plik `PLAN.md` jest używany przez Claude do trackowania zadań.

**Gdy wprowadzasz zmiany:**
1. Aktualizuj `PLAN.md` - zaznacz zrealizowane zadania
2. Dodawaj nowe zadania według priorytetu (High/Medium/Low)
3. Grupuj według obszaru (Docker, Backend, AI, RAG, Frontend, Testing)

**Format:**
```markdown
## Obszar (np. Backend & API)

### Kategoria (np. Performance Optimization)
- [ ] Zadanie do zrobienia
- [x] Zadanie zrealizowane (data: 2025-10-14)
```

## Więcej Informacji

Szczegółowe informacje znajdziesz w:
- **docs/README.md** - Indeks całej dokumentacji
- **docs/DEVOPS.md** - Docker, CI/CD, monitoring, deployment (44KB)
- **docs/TESTING.md** - Test suite (380 testów), fixtures, performance (39KB)
- **docs/RAG.md** - Hybrid Search, GraphRAG, 3 serwisy (38KB)
- **docs/AI_ML.md** - AI/LLM system, persona generation (40KB)
- **docs/TROUBLESHOOTING.md** - Rozwiązywanie problemów (23KB)
- **README.md** - User-facing documentation
