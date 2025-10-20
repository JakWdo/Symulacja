# 📚 Dokumentacja Techniczna - Sight

Indeks dokumentacji technicznej dla deweloperów.

## 📖 Przegląd Dokumentacji

| Dokument | Opis | Rozmiar |
|----------|------|---------|
| [../README.md](../README.md) | User-facing docs, quick start, features | ~800 linii |
| [../CLAUDE.md](../CLAUDE.md) | **Instrukcje dla Claude Code** (architecture, patterns, checklist) | ~260 linii |
| [DOCKER.md](DOCKER.md) | Architektura Docker, multi-stage builds, deployment | ~224 linie |
| [TESTING.md](TESTING.md) | Test suite (208 testów), fixtures, performance | ~998 linii |
| [RAG.md](RAG.md) | System RAG: Hybrid Search + GraphRAG | ~503 linie |
| [../PLAN.md](../PLAN.md) | **Roadmap i zadania dla Claude** (używany do trackowania) | ~350 linii |

---

## 🚀 Quick Links

### Dla Nowych Deweloperów
1. [../README.md](../README.md) - Setup środowiska
2. [DOCKER.md](DOCKER.md) - Docker commands & architecture
3. [../CLAUDE.md](../CLAUDE.md) - Architektura i konwencje
4. [TESTING.md](TESTING.md) - Uruchom testy dla weryfikacji

### Dla Doświadczonych Deweloperów
- **Architektura:** [../CLAUDE.md#architektura](../CLAUDE.md)
- **Docker:** [DOCKER.md](DOCKER.md)
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Testowanie:** [TESTING.md](TESTING.md)
- **RAG System:** [RAG.md](RAG.md)
- **Roadmap:** [../PLAN.md](../PLAN.md)

---

## 📂 Struktura Projektu

```
sight/
├── README.md              # User-facing documentation
├── CLAUDE.md              # Claude Code instructions (architecture, patterns)
├── PLAN.md                # Roadmap & task tracking (używany przez Claude)
│
├── docs/                  # Technical documentation
│   ├── README.md         # Ten plik - indeks dokumentacji
│   ├── DOCKER.md         # Docker architecture & deployment
│   ├── TESTING.md        # Test suite (208 testów)
│   └── RAG.md            # RAG system: Hybrid Search + GraphRAG
│
├── app/                   # Backend (FastAPI)
│   ├── api/              # REST API endpoints
│   ├── core/             # Configuration & constants
│   ├── db/               # Database session & base
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic validation schemas
│   └── services/         # Business logic layer (Service Pattern)
│
├── tests/                 # Test suite (208 testów)
│   ├── unit/             # Unit tests (~150, <5s)
│   ├── integration/      # Integration tests (~35, 10-30s)
│   ├── e2e/              # End-to-end tests (~4, 2-5 min)
│   ├── performance/      # Performance tests (~5, 5-10 min)
│   ├── error_handling/   # Error tests (~9, 5-10s)
│   └── manual/           # Manual test scripts
│
├── frontend/              # Frontend (React + TypeScript)
│   └── src/
│       ├── components/   # React components
│       ├── lib/          # API client & utilities
│       ├── store/        # Zustand store
│       └── types/        # TypeScript types
│
├── scripts/               # Utility scripts
│   ├── init_db.py        # Database initialization
│   └── init_neo4j_indexes.py  # Neo4j index setup
│
├── alembic/               # Database migrations
├── docker-compose.yml     # Development environment
├── docker-compose.prod.yml # Production environment
└── Dockerfile             # Backend multi-stage Dockerfile
```

---

## 🔍 Szczegóły Dokumentacji

### CLAUDE.md - Instrukcje dla Claude

**Plik główny** dla Claude Code podczas pracy z projektem.

**Zawiera:**
- Quick start commands
- Architektura (Service Layer, Event Sourcing, Hybrid Search)
- Konwencje kodu (Python, TypeScript, testy)
- Workflow deweloperski (typowe operacje)
- Zasady production-ready code
- Architecture patterns (6 głównych patternów)
- Common pitfalls & solutions
- Production checklist

**Kiedy czytać:** Zawsze przed rozpoczęciem pracy z projektem.

---

### DOCKER.md - Architektura Docker

**Multi-Stage Builds:**
- Backend: 850MB → 450MB (builder + runtime)
- Frontend: 500MB → 25MB production (deps + builder + dev + prod)

**Key Features:**
- Instant starty (30-60s → <2s) - node_modules cached w image
- Named volume `frontend_node_modules` zapobiega konfliktom
- Hot reload out-of-the-box
- Development vs Production environments

**Performance:**
- Frontend start: <2s (instant!)
- Build cached: ~5-10s
- Hot reload działa natychmiast

---

### TESTING.md - Test Suite

**208 testów** pokrywających wszystkie warstwy.

**Kategorie:**
- **Unit** (~150, <5s) - Services, utilities, models
- **Integration** (~35, 10-30s) - API + DB + External services
- **E2E** (~4, 2-5 min) - Full workflows
- **Performance** (~5, 5-10 min) - Benchmarks i stress tests
- **Error Handling** (~9, 5-10s) - Edge cases & failures

**Coverage:** 80%+ overall, 85%+ dla services

**Cele Wydajnościowe:**
- 20 person < 60s
- Focus group 20×4 < 3 min
- Parallelization speedup >= 3x

---

### RAG.md - System RAG

**Hybrid Search:**
- Vector search (Google Gemini embeddings)
- Keyword search (Neo4j fulltext index)
- RRF Fusion łączy oba wyniki

**GraphRAG:**
- Ekstraktuje wiedzę z dokumentów (węzły + relacje)
- Bogate metadane: description, summary, key_facts, confidence
- LLM-generated Cypher queries

**Użycie:**
- Generator person pobiera kontekst o polskim społeczeństwie
- Graph RAG queries dla analiz

---

### PLAN.md - Roadmap & Task Tracking

**WAŻNE:** Używany przez Claude do trackowania zadań!

**Struktura:**
- Docker & Infrastructure
- Backend & API
- AI & LLM
- RAG & Knowledge Graph
- Frontend
- Testing
- Compliance & Legal
- Priorities (High/Medium/Low)

**Gdy Claude wprowadza zmiany:**
1. Aktualizuje PLAN.md - zaznacza zrealizowane
2. Dodaje nowe zadania według priorytetu
3. Grupuje według obszaru

---

## 🛠️ Dodatkowe Zasoby

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

### Databases
- **PostgreSQL + pgvector:** localhost:5433
- **Redis:** localhost:6379
- **Neo4j Browser:** http://localhost:7474

### Monitoring & Debugging
```bash
# Backend logs
docker-compose logs -f api

# Frontend logs
docker-compose logs -f frontend

# Database migrations
docker-compose exec api alembic upgrade head

# Neo4j indexes
python scripts/init_neo4j_indexes.py

# Test hybrid search
python tests/manual/test_hybrid_search.py
```

---

## 📝 Konwencje Kodowania

### Backend (Python)
- **Style Guide:** PEP 8
- **Type Hints:** Wymagane dla wszystkich funkcji
- **Docstrings:** Język polski (konwencja projektu)
- **Async:** Wszędzie gdzie możliwe (FastAPI + SQLAlchemy async)
- **Abstrakcje:** LangChain dla LLM operations

### Frontend (TypeScript)
- **Components:** Functional components + hooks
- **State Management:** React Query (server) + Zustand (UI)
- **Styling:** Tailwind CSS
- **API Client:** React Query (TanStack Query)

### Testy
- **Framework:** pytest + pytest-asyncio
- **Coverage Target:** 80%+ overall, 85%+ dla services
- **Fixtures:** Shared w conftest.py
- **Markery:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`

---

## 🤝 Contributing

### Przed Pull Requestem
1. ✅ Testy: `pytest tests/ -v -m "not slow"`
2. ✅ Coverage: `pytest tests/ --cov=app --cov-report=html`
3. ✅ Linting (opcjonalnie): `ruff check app/`

### Struktura Commita
```
<type>(<scope>): <subject>

<body>

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** feat, fix, docs, test, refactor, perf, chore

---

## 📞 Kontakt i Wsparcie

**Problemy?**
1. Sprawdź [TESTING.md#rozwiązywanie-problemów](TESTING.md)
2. Przeczytaj [../CLAUDE.md#rozwiązywanie-problemów](../CLAUDE.md)
3. Sprawdź logi: `docker-compose logs`
4. Otwórz issue na GitHubie

---

**Ostatnia aktualizacja:** 2025-10-14
**Wersja dokumentacji:** 3.0
**Liczba testów:** 208
