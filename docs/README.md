# 📚 Dokumentacja Techniczna - Sight

Indeks dokumentacji technicznej dla deweloperów.

## 📖 Przegląd Dokumentacji

| Dokument | Opis | Rozmiar |
|----------|------|---------|
| [../README.md](../README.md) | User-facing docs, quick start, features | ~800 linii |
| [../CLAUDE.md](../CLAUDE.md) | **Instrukcje dla Claude Code** (architecture, patterns, checklist) | ~390 linii |
| [../PLAN.md](../PLAN.md) | **Strategic Roadmap** (27 aktywnych zadań + 9 completed) | ~350 linii |
| [INFRASTRUCTURE.md](INFRASTRUCTURE.md) | **Docker, CI/CD, Cloud Run** (narracyjny styl, all-in-one) | ~700 linii |
| [TESTING.md](TESTING.md) | Test suite (380 testów), fixtures, performance | ~110 linii |
| [RAG.md](RAG.md) | System RAG: Hybrid Search + GraphRAG | ~123 linie |
| [AI_ML.md](AI_ML.md) | AI/LLM system, persona generation, LangChain | ~200 linii |
| [SERVICES.md](SERVICES.md) | Struktura serwisów (domain folders) | ~123 linie |
| [PERSONA_DETAILS.md](PERSONA_DETAILS.md) | Persona Details MVP feature (dokumentacja feature) | ~1057 linii |

---

## 🚀 Quick Links

### Dla Nowych Deweloperów
1. [../README.md](../README.md) - Setup środowiska
2. [INFRASTRUCTURE.md](INFRASTRUCTURE.md) - Docker, CI/CD, Cloud Run
3. [../CLAUDE.md](../CLAUDE.md) - Architektura i konwencje
4. [TESTING.md](TESTING.md) - Uruchom testy dla weryfikacji

### Dla Doświadczonych Deweloperów
- **Architektura:** [../CLAUDE.md#architektura](../CLAUDE.md)
- **Infrastructure:** [INFRASTRUCTURE.md](INFRASTRUCTURE.md) - Docker, CI/CD, Cloud Run
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Testowanie:** [TESTING.md](TESTING.md)
- **RAG System:** [RAG.md](RAG.md)
- **AI/ML:** [AI_ML.md](AI_ML.md)
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
│   ├── INFRASTRUCTURE.md # Docker, CI/CD, Cloud Run (narracyjny)
│   ├── TESTING.md        # Test suite (380 testów)
│   ├── RAG.md            # RAG system: Hybrid Search + GraphRAG
│   ├── AI_ML.md          # AI/LLM system, persona generation
│   ├── SERVICES.md       # Struktura serwisów (domain folders)
│   └── PERSONA_DETAILS.md # Persona Details MVP feature
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

### INFRASTRUCTURE.md - Docker, CI/CD, Cloud Run

**Nowy plik** (2025-10-21) - konsolidacja DEPLOYMENT.md + DEVOPS.md w narracyjny styl.

**Sekcje:**
- **Architektura Docker** - Multi-stage builds, serwisy, resource limits (84% redukcja rozmiaru)
- **Local Development** - Quick start, hot reload, debugging
- **Cloud Run Production** - GCP setup, secrets, single service architecture
- **CI/CD Pipeline** - cloudbuild.yaml (7 kroków), quality gates, monitoring
- **Troubleshooting** - Top 5 problemów + rozwiązania
- **Koszty** - Monthly breakdown (~$16-30), optimization tips

**Performance:**
- Build time: -67% (dzięki layer caching)
- Deployment: 7-12 min (GitHub push → running app)
- Automated: migrations, Neo4j indexes, smoke tests

---

### TESTING.md - Test Suite

**380 testów** pokrywających wszystkie warstwy (narracyjny styl).

**Kategorie:**
- **Unit** (~240, <90s) - Services, utilities, models (w CI/CD)
- **Integration** (~70, 10-30s) - API + DB + External services
- **E2E** (~5, 2-5 min) - Full workflows
- **Performance** (~3, 5-10 min) - Benchmarks i stress tests
- **Error Handling** (~9, 5-10s) - Edge cases & failures

**Coverage:** 80%+ overall, 85%+ dla services

**Cele Wydajnościowe:**
- 20 person < 60s (currently ~45s)
- Focus group 20×4 < 3 min (currently ~2 min)
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

### PLAN.md - Strategic Roadmap

**WAŻNE:** Strategiczny roadmap projektu (20-30 najważniejszych zadań).

**Struktura:**
- Infrastructure & CI/CD (8 zadań)
- Backend & API (6 zadań)
- AI & RAG (6 zadań)
- Frontend (5 zadań)
- Testing & Quality (4 zadania)
- Documentation (3 zadania)
- Priorities (High/Medium/Low - MoSCoW)

**Current Status:**
- 27 aktywnych zadań
- 9 completed (last 30 days)
- Next Sprint Focus: Integration tests w CI/CD, RBAC enforcement, Semantic chunking RAG, Coverage 85%+

**Gdy Claude wprowadza zmiany:**
1. Aktualizuje PLAN.md - zaznacza zrealizowane (data)
2. Dodaje nowe zadania według priorytetu
3. Grupuje według obszaru
4. Usuwa completed >30 dni

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

**Ostatnia aktualizacja:** 2025-10-21
**Wersja dokumentacji:** 4.0
**Liczba testów:** 380
**Struktura:** Narracyjna (ciągły tekst)
