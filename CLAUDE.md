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

## Output Styles & Tryby Pracy

Claude może pracować w różnych trybach w zależności od zadania:

**Default Mode (Debugging/Production):**
- Claude wykonuje zadania samodzielnie
- Pełna implementacja z kodem
- **Używaj dla:** bugfixing, features, refactoring, deployments

**Learning Mode (Edukacyjny):**
- Claude wyjaśnia koncepcje i dostarcza guidance
- User pisze kod samodzielnie z pomocą Claude'a
- Szczegółowe wyjaśnienia "dlaczego" i "jak"
- **Używaj dla:** nauka AI/ML, FastAPI, LangChain, nowych wzorców
- **Aktywacja:** "Use learning output style" lub "/learning"

**Kiedy prosić o Learning Mode:**
- Chcę zrozumieć jak działa AI/ML/RAG
- Uczę się nowej technologii (FastAPI, LangChain)
- Chcę implementować samodzielnie z guidance
- Potrzebuję głębokiego wyjaśnienia architektury

## Dokumentacja

**Główne pliki:**
- **README.md** - User-facing docs, quick start
- **CLAUDE.md** - Ten plik (instrukcje dla Claude)
- **PLAN.md** - Strategic roadmap (20-30 najważniejszych zadań)
- **docs/README.md** - Indeks dokumentacji technicznej
- **docs/DEVOPS.md** - DevOps, Docker, CI/CD, monitoring
- **docs/TESTING.md** - Test suite (380 testów, fixtures, performance)
- **docs/RAG.md** - System RAG (Hybrid Search + GraphRAG)
- **docs/AI_ML.md** - AI/LLM system, persona generation
- **docs/PERSONA_DETAILS.md** - Persona details feature documentation

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

### Wzorce & Common Pitfalls

**Architecture Patterns:**
1. **Service Layer** - Endpoints cienkie, serwisy grube
2. **Async/Await** - Wszędzie dla I/O (LLM, DB, Redis, Neo4j)
3. **Event Sourcing** - Pamięć person (immutable events + embeddings)
4. **Hybrid Search** - Vector + keyword search z RRF fusion
5. **Parallel Processing** - asyncio.gather dla równoległych LLM calls

**Common Pitfalls (UNIKAJ):**
1. **N+1 Queries** → Używaj `selectinload()` dla relations
2. **Token Limits** → Truncate context inteligentnie
3. **Memory Leaks** → Używaj `asyncio.TaskGroup` dla cleanup
4. **Race Conditions** → Redis locks dla concurrent writes
5. **Connection Exhaustion** → Connection pooling + retry logic
6. **Stale Data** → Invalidate React Query cache po mutations

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

1. **Analiza** - Sprawdź istniejącą architekturę w docs/ (lub użyj analityk-biznesowy agent)
2. **Design** - Zaprojektuj rozwiązanie (lub użyj software-architect agent)
3. **Service Layer** - Dodaj logikę w `app/services/`
4. **API Endpoint** - Dodaj endpoint w `app/api/`
5. **Schema** - Dodaj Pydantic schema w `app/schemas/`
6. **Frontend** - Implementuj UI components (React + TypeScript)
7. **Testy** - Dodaj unit + integration tests (pytest)
8. **Review** - Code review + test quality (quality-agent)
9. **Dokumentacja** - Aktualizuj PLAN.md i docs/

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

## Praca z Wyspecjalizowanymi Agentami

Claude ma dostęp do **10 wyspecjalizowanych agentów** do złożonych zadań:

**Quality & Development:**
- **quality-agent** - Code review + test quality assessment (łączy QA + code review)
- **backend-developer** - Python/FastAPI implementation
- **frontend-developer** - React/TypeScript UI components
- **software-architect** - Technical design & architecture

**AI & Specialized:**
- **ai-specialist** - RAG systems, LLM, prompts, LangChain
- **analityk-biznesowy** - Requirements → technical specs (po polsku)
- **projektant-ui-ux** - UI/UX design (shadcn/ui + Tailwind)

**Infrastructure & Security:**
- **inzynier-devops** - Docker, CI/CD, infrastructure
- **specjalista-bezpieczenstwa** - Security audits, vulnerability assessment

**Documentation:**
- **dokumentalista** - Polish technical documentation (bez limitu MD)

**Kiedy i jak używać agentów:**

**Automatyczne użycie:**
Claude automatycznie wybiera agenta gdy:
- Implementujesz nową feature → software-architect + backend/frontend-developer
- Kończysz kod → quality-agent dla code review + test quality
- Modyfikujesz Docker/CI → inzynier-devops
- Pracujesz z RAG/LLM → ai-specialist
- Potrzebujesz specs → analityk-biznesowy

**Jawne wywołanie:**
Możesz poprosić o konkretnego agenta:
```
"Use quality-agent to review this code"
"Use ai-specialist to optimize RAG prompts"
"Use analityk-biznesowy to analyze requirements for X"
"Use inzynier-devops to review Docker setup"
```

**Workflow z agentami:**
1. Nowa feature → analityk-biznesowy (specs) → software-architect (design)
2. Implementacja → backend-developer + frontend-developer
3. Zakończenie → quality-agent (review) + dokumentalista (docs)
4. Deploy → inzynier-devops (infrastructure)

## Zasady Deweloperskie (Production-Ready)

**Code Quality (Must-Have):**
- ✅ Type hints wszędzie (Python), TypeScript strict mode
- ✅ Async/await dla I/O (LLM, DB, Redis, Neo4j)
- ✅ Docstringi po polsku (Google/NumPy style)
- ✅ SOLID principles + DRY
- ✅ Comprehensive error handling
- ✅ Input validation + sanitization

**Testing (>80% Coverage):**
- ✅ Unit tests (isolated components)
- ✅ Integration tests (component interactions)
- ✅ Edge cases + error scenarios
- ✅ Markery: `@pytest.mark.integration`, `@pytest.mark.slow`

## Production Checklist

**Pre-Deploy (Must-Have):**
- [ ] Tests pass (380 tests), coverage >80%
- [ ] Migrations applied, Neo4j indexes created
- [ ] Secrets secure (NIE w .env!), CORS restricted
- [ ] Docker services healthy

**Post-Deploy (Verify):**
- [ ] Smoke tests pass (login, personas, focus group)
- [ ] Performance OK (API <500ms, persona <5s)
- [ ] Monitoring stable (errors <1%, CPU <70%)

## PLAN.md - Strategiczne Zarządzanie Zadaniami

**WAŻNE:** `PLAN.md` to strategiczny roadmap projektu. Utrzymuj 20-30 najważniejszych zadań.

### Kiedy Aktualizować PLAN.md

**✅ Zawsze aktualizuj po:**
- Ukończeniu feature/bugfix/refactor
- Dodaniu nowej funkcjonalności
- Otrzymaniu feedbacku z code review (nowe zadania)
- Znaczących zmianach w architekturze

**⏰ Regularnie:**
- Co tydzień - cleanup completed tasks >30 dni
- Po zakończeniu większego milestone'u
- Gdy lista przekracza 30 zadań (konsoliduj/usuń)

### Jak Aktualizować

**1. Oznaczanie ukończonych:**
```markdown
- [x] Krótki opis ukończonego zadania (data: 2025-10-16)
```

**2. Dodawanie nowych zadań:**
```markdown
- [ ] [Priority: High] Implementacja feature X (1-2 linie opisu)
```

**3. Priorytety:**
- **High** - Blokuje inne zadania, security issues, production bugs
- **Medium** - Ważne features, performance improvements
- **Low** - Nice-to-have, technical debt, minor optimizations

**4. Obszary (Segments):**
- Backend & API
- Frontend
- AI & RAG
- Testing & Quality
- Docker & Infrastructure
- Documentation

### Zasady Utrzymania Planu

**DO:**
- ✅ Trzymaj 20-30 zadań (focused backlog)
- ✅ Używaj konkretnych, actionable descriptions
- ✅ Grupuj podobne zadania w kategorie
- ✅ Aktualizuj po każdym istotnym commit
- ✅ Usuwaj completed tasks starsze niż 30 dni

**DON'T:**
- ❌ Nie dodawaj vague tasks ("poprawić performance")
- ❌ Nie trzymaj >50 zadań (plan staje się bezużyteczny)
- ❌ Nie duplikuj zadań w różnych obszarach
- ❌ Nie zapominaj o datach dla completed tasks

### Format Zadania

```markdown
- [ ] [Priority: 85/100 lub High/Medium/Low] Implementacja hybrid search z RRF fusion dla RAG (max 2 linie)
```

## Więcej Informacji

Szczegółowe informacje znajdziesz w:
- **docs/README.md** - Indeks całej dokumentacji technicznej
- **docs/DEVOPS.md** - Docker, CI/CD, monitoring, deployment
- **docs/TESTING.md** - Test suite (380 testów), fixtures, performance
- **docs/RAG.md** - Hybrid Search, GraphRAG, 3 serwisy RAG
- **docs/AI_ML.md** - AI/LLM system, persona generation, LangChain
- **docs/PERSONA_DETAILS.md** - Persona details MVP feature
- **README.md** - User-facing documentation, quick start
