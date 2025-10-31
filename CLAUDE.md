# CLAUDE.md

Instrukcje dla Claude Code podczas pracy z tym projektem.

## Przegląd Projektu

**Sight** - Platforma do wirtualnych grup fokusowych z AI.

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
- **PLAN.md** - Strategic roadmap (27 aktywnych zadań + 9 completed)
- **docs/README.md** - Indeks dokumentacji technicznej
- **docs/INFRASTRUCTURE.md** - **NOWY** - Docker, CI/CD, Cloud Run, monitoring (narracyjny styl)
- **docs/SERVICES.md** - Struktura serwisów (reorganizacja 2025-10-20)
- **docs/TESTING.md** - Test suite (380 testów, fixtures, performance)
- **docs/RAG.md** - System RAG (Hybrid Search + GraphRAG)
- **docs/AI_ML.md** - AI/LLM system, persona generation
- **docs/PERSONA_DETAILS.md** - Persona details feature documentation

## Architektura

### Service Layer Pattern

```
API Endpoints (app/api/*.py) - validation, routing
    ↓
Service Layer (app/services/domain/*.py) - business logic
    ↓
Models/DB (app/models/*.py) - data access
```

**Nowa struktura (2025-10-20):** Serwisy pogrupowane w foldery:
- `app/services/shared/` - Wspólne (LLM clients)
- `app/services/personas/` - Zarządzanie personami
- `app/services/focus_groups/` - Grupy fokusowe
- `app/services/rag/` - RAG & Knowledge Graph
- `app/services/surveys/` - Ankiety

**Import (nowy):**
```python
from app.services.personas import PersonaGeneratorLangChain, SegmentBriefService
from app.services.rag import PolishSocietyRAG
```

### Kluczowe Serwisy

**Personas:**
- `PersonaGeneratorLangChain` - Generuje persony z RAG + statistical sampling
- `SegmentBriefService` - Briefe segmentów (Redis cache 7 dni, storytelling)
- `PersonaDetailsService` - Detail View orchestrator
- `PersonaNeedsService` - JTBD analysis

**Focus Groups:**
- `FocusGroupServiceLangChain` - Orkiestracja dyskusji (async parallelization)
- `MemoryServiceLangChain` - Event sourcing z semantic search

**RAG:**
- `RAGDocumentService` - Zarządzanie dokumentami (ingest, CRUD)
- `GraphRAGService` - Graph RAG (Cypher queries, answer_question)
- `PolishSocietyRAG` - Hybrid search (vector + keyword + RRF fusion)

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
DATABASE_URL=postgresql+asyncpg://sight:password@postgres:5432/sight_db
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Security (ZMIEŃ W PRODUKCJI!)
SECRET_KEY=change-me
ENVIRONMENT=development
DEBUG=true

# LLM Models
DEFAULT_MODEL=gemini-2.5-flash
TEMPERATURE=0.7
MAX_TOKENS=6000

# Embeddings (RAG System)
# CRITICAL: Must include "models/" prefix for LangChain Google AI
EMBEDDING_MODEL=models/gemini-embedding-001

# RAG Configuration
RAG_ENABLED=True
RAG_USE_HYBRID_SEARCH=True
RAG_VECTOR_WEIGHT=0.7
RAG_TOP_K=8
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=300
```

**UWAGA:** `EMBEDDING_MODEL` **MUSI** zawierać prefix `"models/"` dla Google Generative AI przez LangChain. Bez tego prefiksu API zwróci błąd:
```
400 * BatchEmbedContentsRequest.model: unexpected model name format
```

## Internationalization (i18n)

Aplikacja wspiera pełną dwujęzyczność (Polski/Angielski) zarówno w UI jak i treści generowanej przez AI.

### Frontend i18n

**Biblioteki:**
- `i18next` - Core library
- `react-i18next` - React integration
- `i18next-browser-languagedetector` - Auto-detection i localStorage persistence

**Struktura plików:**
```
frontend/src/i18n/
├── index.ts              # Config i18next
├── hooks.ts              # Custom hooks (useLanguage, useNamespacedTranslation)
├── types.ts              # TypeScript types (Language, LANGUAGES)
└── locales/
    ├── pl/               # Polskie tłumaczenia
    │   ├── common.json   # Wspólne elementy (sidebar, buttons, validation)
    │   ├── auth.json     # Login/Register
    │   ├── settings.json # Ustawienia
    │   ├── dashboard.json
    │   ├── projects.json
    │   ├── personas.json
    │   ├── surveys.json
    │   └── focus-groups.json
    └── en/               # Angielskie tłumaczenia (ta sama struktura)
```

**Użycie w komponentach:**
```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation('dashboard');

  return (
    <div>
      <h1>{t('header.title')}</h1>
      <p>{t('header.subtitle')}</p>
    </div>
  );
}
```

**Formatowanie dat:**
```tsx
import { useDateFormat } from '@/hooks/useDateFormat';

const { formatDate, formatRelativeTime } = useDateFormat();
const formattedDate = formatDate(createdAt); // Automatycznie pl-PL lub en-US
const relativeTime = formatRelativeTime(updatedAt); // "2 godz. temu" / "2 hrs ago"
```

**Przełącznik języka:**
- `<LanguageToggle />` w AppSidebar (dropdown z flagkami)
- `<LanguageSelector />` w Settings (przyciski)
- Synchronizacja z backendem (PUT /settings/profile z preferred_language)

### Backend i18n

**Middleware locale:**
```python
from app.middleware.locale import get_locale

@router.post("/some-endpoint")
async def some_endpoint(
    locale: str = Depends(get_locale),
    current_user: User = Depends(get_current_user)
):
    # locale zawiera 'pl' lub 'en' z Accept-Language header
    # Fallback: user.preferred_language → default 'pl'
    result = await some_service.do_something(locale=locale)
    return result
```

**AI Language Detection:**
- Focus Groups automatycznie wykrywają język z pytań i odpowiedzi
- Funkcja `detect_input_language()` w `discussion_summarizer.py`
- AI generuje treść w wykrytym języku (nagłówki sekcji pozostają po angielsku dla parsera)

**Priority logic:**
1. `Accept-Language` header (wysyłany przez frontend)
2. `current_user.preferred_language` (z bazy danych)
3. Default: `'pl'`

**Normalizacja:**
- `'pl-PL'` → `'pl'`
- `'en-US'` → `'en'`
- Niewspierane języki → fallback `'pl'`

### Dodawanie Nowych Tłumaczeń

**1. Dodaj klucze do JSON:**
```json
// frontend/src/i18n/locales/pl/projects.json
{
  "list": {
    "title": "Projekty",
    "empty": "Brak projektów"
  }
}

// frontend/src/i18n/locales/en/projects.json
{
  "list": {
    "title": "Projects",
    "empty": "No projects"
  }
}
```

**2. Użyj w komponencie:**
```tsx
const { t } = useTranslation('projects');
<h1>{t('list.title')}</h1>
```

**3. Parametryzacja:**
```json
{
  "welcome": "Witaj, {{name}}!",
  "count": "{{count}} elementów"
}
```

```tsx
{t('welcome', { name: user.name })}
{t('count', { count: items.length })}
```

### Testing i18n

**Frontend:**
```bash
npm run dev
# Przełącz język w UI (sidebar lub settings)
# Sprawdź czy wszystkie stringi się zmieniają
# Odśwież stronę → język powinien persist (localStorage)
```

**Backend:**
```bash
# Testy middleware
pytest tests/unit/test_locale_middleware.py -v

# Testy language detection
pytest tests/unit/test_language_detection.py -v

# Test z headerem Accept-Language
curl -H "Accept-Language: en-US" http://localhost:8000/api/v1/projects
```

### Przetłumaczone Komponenty (Status: 2025-10-31)

**✅ COMPLETE - Core Features (100%):**
- **Core UI:** AppSidebar, Login/Register, AuthContext, Settings (all sections), AppLoader, LanguageToggle
- **Dashboard:** FigmaDashboard, DashboardHeader, ActiveProjectsSection, LatestInsightsSection, NotificationsSection, UsageBudgetSection, HealthBlockersSection, InsightDetailModal, InsightAnalyticsCharts
- **Personas:** PersonaGenerationWizard, PersonaDetailsDrawer, NeedsSection, ProfileSection, PersonaReasoningPanel, DeletePersonaDialog, ComparePersonasDialog, MessagingGeneratorDialog, InsightsSection
- **Focus Groups:** FocusGroupBuilder, FocusGroupView (complete - all tabs), FocusGroupAnalysisView (all tabs), ExecutiveSummaryCard, KeyInsightsGrid, SegmentCard, SurprisingFindingsCard, RecommendationItem, AISummaryPanel, ResponsesList, ResponseCard, ResponseFilters
- **Surveys:** SurveyBuilder (complete builder), SurveyResults
- **Projects:** ProjectPanel, DeleteProjectDialog, UndoDeleteDialog
- **Analysis:** BusinessMetricsOverview, MetricCardWithExplanation, PersonaInsightDrawer
- **RAG:** RAGManagementPanel

**📊 Translation Coverage:**
- **Namespaces:** 11 complete (common, dashboard, personas, projects, focus-groups, surveys, settings, auth, analysis, rag, charts)
- **Translation Keys:** ~2,500+ keys (PL + EN)
- **Components Using i18n:** 60+ components
- **Test Coverage:** Comprehensive i18n tests in `frontend/src/__tests__/i18n.test.tsx`

**⚠️ ARCHIVED/PARTIAL:**
- **GraphAnalysis.tsx** - 30% translated (archived feature per CLAUDE.md)
- **Minor UI utilities** - FloatingControls, StatsOverlay, PageHeader (minimal/no user-facing strings)

**🎯 Implementation Quality:**
- ✅ Zero hardcoded strings in active features
- ✅ Consistent key structure across namespaces
- ✅ Parameter interpolation for dynamic content (e.g., `{{count}}`, `{{name}}`)
- ✅ Plural forms where needed
- ✅ Date/time formatting with locale support
- ✅ All translations verified with automated tests

### Fallback Strategy

**Brakujące tłumaczenia:** Pokazuj klucz translacyjny (np. `'settings.profile.title'`)
- Development-friendly - od razu wiadomo co trzeba przetłumaczyć
- Console warning w dev mode

### Performance

- Bundle size increase: ~100KB (wszystkie translation files)
- Lazy loading: Możliwe (ale nie zaimplementowane - wszystkie namespaces ładowane od razu)
- Build time: Nie ma wpływu (JSON importowane statycznie)

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
- **docs/INFRASTRUCTURE.md** - Docker, CI/CD, Cloud Run, monitoring (narracyjny styl)
- **docs/TESTING.md** - Test suite (380 testów), fixtures, performance
- **docs/RAG.md** - Hybrid Search, GraphRAG, 3 serwisy RAG
- **docs/AI_ML.md** - AI/LLM system, persona generation, LangChain
- **docs/PERSONA_DETAILS.md** - Persona details MVP feature
- **PLAN.md** - Strategic roadmap (27 aktywnych zadań)
- **README.md** - User-facing documentation, quick start
