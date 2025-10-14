# 📚 Dokumentacja Techniczna - Market Research SaaS

Witaj w dokumentacji technicznej platformy Market Research SaaS!

## 📖 Przegląd Dokumentacji

Ten folder zawiera szczegółową dokumentację techniczną dla deweloperów i zaawansowanych użytkowników.

### Główne Dokumenty

| Dokument | Opis | Dla Kogo |
|----------|------|----------|
| [../README.md](../README.md) | Główna dokumentacja użytkownika, quick start, features | Wszyscy użytkownicy |
| [../CLAUDE.md](../CLAUDE.md) | Kompletna dokumentacja deweloperska, architektura, API | Deweloperzy |
| [TESTING.md](TESTING.md) | Dokumentacja testów (unit, integration, e2e, performance) | QA, Deweloperzy |
| [RAG.md](RAG.md) | System RAG: Hybrid Search + GraphRAG | AI/ML Engineers |
| [DOCKER.md](DOCKER.md) | Architektura Docker, multi-stage builds, deployment | DevOps, Deweloperzy |
| [PLAN.md](PLAN.md) | Roadmap & future improvements (Docker, AI, Frontend, etc.) | Product, Deweloperzy |

---

## 🚀 Quick Links

### Dla Nowych Deweloperów
1. Zacznij od [../README.md](../README.md) - setup środowiska
2. Przeczytaj [DOCKER.md](DOCKER.md) - Docker architecture & commands
3. Przeczytaj [../CLAUDE.md](../CLAUDE.md) - architektura i konwencje
4. Uruchom testy z [TESTING.md](TESTING.md) - weryfikacja środowiska

### Dla Doświadczonych Deweloperów
- **Docker:** [DOCKER.md](DOCKER.md) - Multi-stage builds, deployment
- **Architektura:** [../CLAUDE.md#architektura](../CLAUDE.md)
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Testowanie:** [TESTING.md](TESTING.md)
- **RAG System:** [RAG.md](RAG.md)
- **Roadmap:** [PLAN.md](PLAN.md) - Future improvements

---

## 📂 Struktura Projektu

```
market-research-saas/
├── README.md              # User-facing documentation
├── CLAUDE.md              # Complete developer guide
│
├── docs/                  # Technical documentation (you are here)
│   ├── README.md         # This file - documentation index
│   ├── TESTING.md        # Test suite documentation (208 tests)
│   ├── RAG.md            # RAG system: Hybrid Search + GraphRAG
│   ├── DOCKER.md         # Docker architecture & deployment
│   └── PLAN.md           # Roadmap & future improvements
│
├── app/                   # Backend application
│   ├── api/              # FastAPI endpoints
│   ├── core/             # Configuration & constants
│   ├── db/               # Database session & base
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic validation schemas
│   └── services/         # Business logic layer
│
├── tests/                 # Test suite
│   ├── unit/             # Unit tests (~150 tests, <5s)
│   ├── integration/      # Integration tests with DB (~35 tests, 10-30s)
│   ├── e2e/              # End-to-end tests (~4 tests, 2-5 min)
│   ├── performance/      # Performance benchmarks (~5 tests, 5-10 min)
│   ├── error_handling/   # Error & resilience tests (~9 tests, 5-10s)
│   ├── manual/           # Manual test scripts
│   └── conftest.py       # Shared fixtures
│
├── scripts/               # Utility scripts
│   ├── init_db.py        # Database initialization
│   └── init_neo4j_indexes.py  # Neo4j index setup
│
├── alembic/               # Database migrations
└── frontend/              # React + TypeScript frontend
```

---

## 🔍 Szczegóły Dokumentacji

### Docker ([DOCKER.md](DOCKER.md))

Dokumentacja architektury Docker z multi-stage builds.

**Key Features:**
- Multi-stage builds: Backend (builder + runtime), Frontend (deps + builder + dev + production)
- Image sizes: Backend 450MB, Frontend prod 25MB
- Named volumes dla frontend node_modules (unika konfliktów)
- docker-compose.yml (development) + docker-compose.prod.yml (production)

**Performance:**
- Frontend starty: 30-60s → <2s (instant!)
- Build times (cached): ~5-10s
- Hot reload działa out-of-the-box

---

### System RAG ([RAG.md](RAG.md))

Dokumentacja systemu RAG łączącego Hybrid Search i GraphRAG.

**Hybrid Search:**
- Vector search (Google Gemini embeddings) + Keyword search (Neo4j fulltext)
- RRF Fusion łączy oba wyniki
- Użycie: Generator person pobiera kontekst o polskim społeczeństwie

**GraphRAG:**
- Ekstraktuje wiedzę z dokumentów (węzły + relacje)
- Bogate metadane: description, summary, key_facts, confidence_level
- LLM-generated Cypher queries

---

### Testowanie ([TESTING.md](TESTING.md))

Test suite: 208 testów pokrywających wszystkie warstwy.

**Kategorie:**
- Unit Tests (~150, <5s)
- Integration Tests (~35, 10-30s)
- E2E Tests (~4, 2-5 min)
- Performance Tests (~5, 5-10 min)

**Cele Wydajnościowe:**
- 20 person < 60s
- Focus group 20×4 < 3 min
- Parallelization speedup >= 3x

---

### Roadmap ([PLAN.md](PLAN.md))

Plan rozwoju z podziałem na obszary:
- **Docker:** CI/CD, Registry, Kubernetes, Monitoring
- **Backend:** Performance, API enhancements, Security
- **AI/LLM:** Multi-model support, Token optimization
- **RAG:** Hybrid search improvements, Graph enhancements
- **Frontend:** UI/UX, Real-time features, Accessibility
- **Testing:** Coverage 90%+, E2E, Performance

---

## 🛠️ Dodatkowe Zasoby

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Schema:** http://localhost:8000/openapi.json

### Database
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
- **Docstrings:** Język polski (istniejąca konwencja)
- **Async:** Wszędzie gdzie możliwe (FastAPI + SQLAlchemy async)
- **Abstrakcje:** LangChain dla LLM operations

### Frontend (TypeScript)
- **Style Guide:** Airbnb TypeScript
- **Components:** Functional components + hooks
- **State Management:** Zustand
- **Styling:** Tailwind CSS
- **API Client:** React Query (TanStack Query)

### Testy
- **Framework:** pytest + pytest-asyncio
- **Coverage Target:** 85%+ overall, 90%+ dla services
- **Fixtures:** Shared w conftest.py
- **Markery:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`

---

## 🤝 Contributing

### Przed Pull Requestem
1. ✅ Uruchom testy: `pytest tests/ -v -m "not slow"`
2. ✅ Sprawdź coverage: `pytest tests/ --cov=app --cov-report=html`
3. ✅ Type checking: `mypy app/` (jeśli zainstalowane)
4. ✅ Linting: `ruff check app/` (opcjonalnie)

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
2. Przeczytaj [CLAUDE.md#rozwiązywanie-problemów](../CLAUDE.md)
3. Sprawdź logi: `docker-compose logs`
4. Otwórz issue na GitHubie

**Dokumentacja:**
- Main: [README.md](../README.md)
- Developer: [CLAUDE.md](../CLAUDE.md)
- Docker: [DOCKER.md](DOCKER.md)
- Tests: [TESTING.md](TESTING.md)
- RAG: [RAG.md](RAG.md)
- Roadmap: [PLAN.md](PLAN.md)

---

**Ostatnia aktualizacja:** 2025-10-14
**Wersja dokumentacji:** 2.1
**Liczba testów:** 208
