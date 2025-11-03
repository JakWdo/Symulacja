# Dokumentacja Techniczna - Sight

Indeks dokumentacji dla platformy Sight - wirtualnych grup fokusowych napędzanych sztuczną inteligencją. Dokumentacja jest zorganizowana w 6 głównych plikach, każdy ~800 linii, napisany w naturalnym, narracyjnym stylu.

## Dokumentacja Główna

| Dokument | Opis | Rozmiar |
|----------|------|---------|
| [AI_ML.md](AI_ML.md) | Architektura AI/ML: LLM, RAG, prompty, optymalizacje, SLA | ~750 linii |
| [BACKEND.md](BACKEND.md) | Architektura backendu: API, serwisy, baza danych, autentykacja | ~850 linii |
| [BIZNES.md](BIZNES.md) | Model biznesowy, ROI, GTM strategy, roadmap i priorytety | ~810 linii |
| [INFRASTRUKTURA.md](INFRASTRUKTURA.md) | Docker, CI/CD, Cloud Run, monitoring, logowanie | ~850 linii |
| [QA.md](QA.md) | Testowanie: piramida testów, fixtures, metryki, troubleshooting | ~710 linii |
| [ROADMAP.md](ROADMAP.md) | Strategiczny roadmap na 2025: Q1-Q4, priorytety, milestones | ~550 linii |

**Uwaga:** Każdy plik jest skondensowany do ~800 linii dla czytelności. Zawiera sekcje omówienia, wzorce i kluczowe szczegóły bez powtórzeń między plikami.

---

## Quick Links

### Dla Nowych Deweloperów

1. **[../CLAUDE.md](../CLAUDE.md)** - Setup środowiska, komendy, architektura wysokiego poziomu (zacznij tutaj!)
2. **[BACKEND.md](BACKEND.md)** - Jak działa backend: API, serwisy, baza danych
3. **[INFRASTRUKTURA.md](INFRASTRUKTURA.md)** - Docker, uruchamianie lokalnie, deployment
4. **[QA.md](QA.md)** - Jak uruchomić testy i zweryfikować setup

### Dla Doświadczonych Deweloperów

**Architektura Techniczna:**
- [BACKEND.md](BACKEND.md) - API, serwisy, database, auth, events
- [AI_ML.md](AI_ML.md) - LLM, RAG, prompty, optimizations, SLA targets
- [INFRASTRUKTURA.md](INFRASTRUKTURA.md) - Docker, Cloud Run, CI/CD, monitoring

**Strategia i Biznes:**
- [BIZNES.md](BIZNES.md) - Model biznesowy, GTM, finansowe projekcje
- [ROADMAP.md](ROADMAP.md) - Priorytety na 2025, completed tasks, blocked items

**Operacje i Jakość:**
- [QA.md](QA.md) - Test suite overview, metryki pokrycia, troubleshooting

**API i Tools:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Neo4j Browser: http://localhost:7474

---

## Przegląd Dokumentacji

### AI_ML.md - Architektura AI/ML

Kompletna dokumentacja systemu AI/ML platformy (~750 linii).

**Sekcje:**
- Model Selection Strategy (Flash vs Pro, kiedy użyć każdego)
- LLM Infrastructure (LangChain, retries, error handling)
- RAG System Architecture (Hybrid Search + Graph RAG)
- Prompt Engineering (patterns, validation, optimization)
- Performance Optimizations (parallel calls, caching, compression)
- Token Usage & Cost Management (tracking, budgeting)
- Monitoring & Observability (SLA targets, metrics)

**Performance SLA Targets:**
- Generacja person: <60s (20 osób) ✅
- Dyskusja grupy fokusowej: <3min (20×4 pytania) ✅
- Zapytania RAG: <5s (Graph RAG) ✅
- Odpowiedzi API: <500ms (p90)

---

### BACKEND.md - Architektura Backendu

Dokumentacja całego backendu FastAPI (~850 linii).

**Sekcje:**
- API Layer (REST endpoints, routing, validation, error handling)
- Service Layer (Business logic, domain services)
  - Personas (generacja, orkiestracja, potrzeby)
  - Focus Groups (dyskusje, podsumowania, pamięć)
  - Surveys (generacja odpowiedzi)
  - RAG (wyszukiwanie hybrydowe, transformacje grafowe)
- Database Layer (PostgreSQL, pgvector, SQLAlchemy async)
- Authentication & Authorization (JWT, hashing)
- Event Sourcing (persona events, audit trail)
- Background Jobs (cleanup, scheduled tasks)
- Integration Points (LLM, Neo4j, Redis)

**Kluczowe wzorce:**
- Service Layer Pattern dla separacji logiki biznesowej
- Event Sourcing dla ścieżki audytu
- Async-first design z SQLAlchemy 2.0
- Dependency Injection przez FastAPI

---

### BIZNES.md - Model Biznesowy

Analiza biznesowa i strategia platformy (~810 linii).

**Sekcje:**
- Value Proposition (problem, rozwiązanie, USP)
- Market Analysis (TAM/SAM/SOM, konkurencja, positioning)
- Business Model (revenue streams, pricing tiers, unit economics)
- GTM Strategy (customer acquisition, channels, partnerships)
- Financial Projections (ROI analysis, costs, revenue forecast)
- Risk Analysis (mitigation strategies, dependencies)
- KPIs i Success Metrics

**Kluczowe metryki:**
- LTV:CAC ratio targets
- Customer acquisition cost breakdown
- Revenue per customer projections
- Market penetration strategy

---

### INFRASTRUKTURA.md - Infrastruktura

Dokumentacja deploymetu, CI/CD i monitoringu (~850 linii).

**Sekcje:**
- Docker Architecture (multi-stage builds, serwisy, resource limits)
- Local Development (quick start, hot reload, debugging)
- Cloud Run Production (GCP deployment, secrets management)
- CI/CD Pipeline (GitHub → Cloud Build → Cloud Run)
- Monitoring & Logging (Cloud Logging, error tracking)
- Performance Optimizations (image size, build time, deployment time)

**Performance Wins:**
- Build time: -67% (layer caching)
- Deployment: 7-12 min (GitHub push → running app)
- Image size: -84% (multi-stage builds)

---

### QA.md - Testowanie

Dokumentacja strategii testowania i QA (~710 linii).

**Sekcje:**
- Piramida Testów (80% unit, 14% integration, 3% E2E)
- Test Suite Overview (444 testy w 5 kategoriach)
- Shared Fixtures (setup, teardown, mock data)
- Coverage Metrics (87% overall, targets per module)
- Performance Benchmarks (SLA targets, current results)
- Running Tests (komendy, CI/CD integration)
- Troubleshooting (Top 5 common issues)
- Roadmap QA na 2025

**Test Suite Stats:**
- 444 testy (355 unit, 63 integration, 12 E2E, 5 performance, 9 error handling)
- Pokrycie: 87% overall, 92% personas, 89% focus groups
- Czas: <90s fast tests, 5-10 min full suite

---

### ROADMAP.md - Strategiczny Roadmap

Roadmap platformy na rok 2025 (~550 linii).

**Struktura:**
- Q1 2025 - MVP features, core infrastructure
- Q2 2025 - Advanced features, integrations
- Q3 2025 - Scale & optimization
- Q4 2025 - Enterprise features

**Śledzenie postępów:**
- Completed tasks (completed, z datami)
- In-progress tasks (status,% completion)
- Blocked tasks (reason, mitigation)
- Upcoming priorities (quarterly)

---

## Struktura Projektu

```
sight/
├── README.md              # User-facing documentation
├── CLAUDE.md              # Claude Code instructions (architektura, wzorce)
│
├── docs/                  # Technical documentation
│   ├── README.md         # Ten plik - indeks dokumentacji
│   ├── AI_ML.md          # AI/ML architecture (~750 linii)
│   ├── BACKEND.md        # Backend architecture (~850 linii)
│   ├── BIZNES.md         # Business model & strategy (~810 linii)
│   ├── INFRASTRUKTURA.md # Infrastructure & CI/CD (~850 linii)
│   ├── QA.md             # Testing & QA (~710 linii)
│   ├── ROADMAP.md        # Strategic roadmap 2025 (~550 linii)
│   │
│   └── archive/          # Zarchiwizowana dokumentacja
│       └── persona_details_v3.md
│
├── app/                   # Backend (FastAPI)
│   ├── api/              # REST API endpoints
│   ├── core/             # Configuration & security
│   ├── db/               # Database session
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic validation
│   ├── services/         # Business logic (Service Layer)
│   │   ├── personas/     # Persona generation
│   │   ├── focus_groups/ # Focus group discussions
│   │   ├── surveys/      # Survey responses
│   │   ├── rag/          # RAG & search
│   │   └── dashboard/    # Usage tracking
│   └── tasks/            # Background jobs
│
├── tests/                 # Test suite
│   ├── unit/             # Unit tests (~240)
│   ├── integration/      # Integration tests (~70)
│   ├── e2e/              # End-to-end tests (~5)
│   ├── performance/      # Performance tests (~3)
│   └── error_handling/   # Error tests (~9)
│
├── config/                # Centralized configuration (YAML)
│   ├── models.yaml       # Model registry & fallback
│   ├── features.yaml     # Feature flags & targets
│   ├── prompts/          # 25+ prompts by domain
│   └── rag/              # RAG configuration
│
├── frontend/              # Frontend (React + TypeScript)
│   └── src/
│       ├── components/   # React components
│       ├── lib/          # API client & utilities
│       ├── store/        # Zustand store
│       └── types/        # TypeScript types
│
├── scripts/               # Utility scripts
│   ├── init_neo4j_indexes.py  # Neo4j setup
│   └── archive/               # Legacy scripts
│
├── alembic/               # Database migrations
├── docker-compose.yml     # Development environment
└── Dockerfile             # Backend Dockerfile
```

---

## Archiwum

| Dokument | Opis | Status |
|----------|------|--------|
| [archive/persona_details_v3.md](archive/persona_details_v3.md) | Stara dokumentacja Persona Details MVP | Zarchiwizowany |

---

## Konwencje Kodowania

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

### Testy
- **Framework:** pytest + pytest-asyncio
- **Coverage Target:** 80%+ overall, 85%+ dla services
- **Fixtures:** Shared w conftest.py
- **Markery:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`

---

## API i Narzędzia

**API Documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

**Databases:**
- PostgreSQL + pgvector: localhost:5433
- Redis: localhost:6379
- Neo4j Browser: http://localhost:7474

**Monitoring & Debugging:**
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

## Contributing

### Przed Pull Requestem
1. ✅ Testy: `pytest tests/ -v -m "not slow"`
2. ✅ Coverage: `pytest tests/ --cov=app --cov-report=html`
3. ✅ Linting: `ruff check app/`

### Struktura Commita
```
<type>(<scope>): <subject>

<body>

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** feat, fix, docs, test, refactor, perf, chore

---

## Problemy?

1. Sprawdź [QA.md](QA.md) - Troubleshooting testów (Top 5 problemów)
2. Sprawdź [INFRASTRUKTURA.md](INFRASTRUKTURA.md) - Troubleshooting infrastruktury
3. Przeczytaj [../CLAUDE.md](../CLAUDE.md) - Częste pułapki i rozwiązania
4. Sprawdź logi: `docker-compose logs`
5. Otwórz issue na GitHubie

---

**Ostatnia aktualizacja:** 2025-11-03
**Wersja dokumentacji:** 6.0
**Struktura:** Płaska (6 głównych plików)
**Całkowita liczba linii:** ~4,520 linii dokumentacji
