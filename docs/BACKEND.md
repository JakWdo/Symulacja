# Architektura Backendu - Platforma Sight

## Przegląd

**Sight** to platforma badań rynkowych wykorzystująca AI do generowania syntetycznych person i symulacji grup fokusowych. Backend oparty jest na **FastAPI** z architekturą async-first, zorganizowaną według wzorca **Service Layer Pattern**.

### Stack Technologiczny

**Core Framework:**
- FastAPI (async Python framework)
- Python 3.11+ (native async/await)
- Pydantic (walidacja danych)

**Bazy Danych:**
- PostgreSQL + pgvector (główna baza + embeddingi)
- Neo4j (baza grafowa dla RAG)
- Redis (cache wyników LLM)

**AI/ML Stack:**
- Google Gemini 2.5 (Flash dla generacji, Pro dla analiz)
- LangChain (orkiestracja LLM)
- pgvector (wyszukiwanie embeddingów 768D)

**Infrastruktura:**
- SQLAlchemy 2.0 (async ORM)
- Alembic (migracje DB)
- APScheduler (background jobs)
- python-jose (JWT tokens)
- bcrypt (hashowanie haseł)

### Kluczowe Liczby

| Metryka | Wartość |
|---------|---------|
| Linie kodu API | ~5,130 |
| Linie kodu Services | ~14,380 |
| Liczba endpointów | ~60+ |
| Liczba modeli DB | 16 |
| Liczba serwisów | 30+ |
| Promptów LLM | 25+ |

---

## Diagram Architektury

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  (React SPA, HTTP Requests, JWT Authentication)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   MIDDLEWARE    │
                    ├─────────────────┤
                    │ CORS            │ (Development only)
                    │ Request ID      │ (Correlation tracking)
                    │ Security Headers│ (OWASP best practices)
                    │ Rate Limiting   │ (slowapi)
                    └────────┬────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                         API LAYER                                │
│                   (app/api/ - ~5,130 LOC)                        │
├──────────────────────────────────────────────────────────────────┤
│  Auth | Projects | Personas | Focus Groups | Surveys            │
│  RAG | Analysis | Dashboard                                      │
│                                                                   │
│  Cechy: Thin controllers, dependency injection, Pydantic         │
│         schemas, error handling, logging                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  DEPENDENCIES   │
                    ├─────────────────┤
                    │ get_current_user│ (JWT validation)
                    │ get_db          │ (DB session)
                    │ get_project_*   │ (Authorization)
                    └────────┬────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                       SERVICE LAYER                              │
│                 (app/services/ - ~14,380 LOC)                    │
├──────────────────────────────────────────────────────────────────┤
│  personas/ → orchestration, generator, validator, needs          │
│  focus_groups/ → service, summarizer, memory                     │
│  surveys/ → response_gen                                         │
│  rag/ → hybrid_search, graph_service, document                   │
│  dashboard/ → orchestrator, metrics, health, usage_logging       │
│  maintenance/ → cleanup (scheduled)                              │
│  shared/ → clients (LLM), rag_provider                           │
│                                                                   │
│  Logika biznesowa, wywołania LLM, transformacje                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
            ┌────────────────┴───────────────┐
            │                                │
┌───────────▼──────────┐          ┌─────────▼──────────┐
│   EXTERNAL SERVICES  │          │    DATA LAYER      │
├──────────────────────┤          ├────────────────────┤
│ • Gemini API (LLM)   │          │ • User, Project    │
│ • Neo4j Graph DB     │          │ • Persona          │
│ • Redis Cache        │          │ • PersonaEvent     │
└──────────────────────┘          │ • FocusGroup       │
                                  │ • Survey, RAG      │
                                  │ • Dashboard*       │
                                  │                    │
                                  │ SQLAlchemy ORM     │
                                  └─────────┬──────────┘
                                            │
                                  ┌─────────▼──────────┐
                                  │   POSTGRESQL       │
                                  │   + pgvector       │
                                  │ Pool: 5 + 10       │
                                  └────────────────────┘
```

**Przepływ Danych:**
```
Client → Middleware (request_id, headers) → API (validate) → Dependencies (auth, DB)
→ Service (business logic) → [DB + LLM + RAG + Cache] → Response
```

---

## Warstwa API

**Lokalizacja:** `app/api/` (~5,130 LOC)
**Rola:** Thin controllers - walidacja, autentykacja, delegacja

### Struktura Modułów

```
app/api/
├── auth.py                  # Register, login, logout, /me
├── projects.py              # CRUD projektów
├── personas/                # Modularyzowany (PR2)
│   ├── crud.py              # List, delete, bulk-delete, undo
│   ├── generation.py        # Generate endpoint
│   ├── details.py           # Details, reasoning, archived
│   └── helpers.py           # Shared utilities
├── focus_groups.py          # Dyskusje fokusowe
├── surveys.py               # Ankiety syntetyczne
├── analysis.py              # Analizy AI
├── rag.py                   # Upload, search
├── workflows.py             # Workflow Builder (11 endpoints)
├── dashboard.py             # Metryki, health, usage
├── settings.py              # Ustawienia użytkownika
├── dependencies.py          # DI (auth, authorization)
└── exception_handlers.py    # Centralized error handling
```

### Kluczowe Endpointy

```python
# Auth
POST   /auth/register, /auth/login
GET    /auth/me

# Projects
POST   /projects
GET    /projects, /projects/{id}
DELETE /projects/{id}, POST /projects/{id}/undo-delete

# Personas
POST   /projects/{id}/personas/generate  # Background task
GET    /projects/{id}/personas, /personas/{id}
GET    /personas/{id}/reasoning           # Wyjaśnienie LLM
DELETE /personas/{id}

# Focus Groups
POST   /projects/{id}/focus-groups
POST   /focus-groups/{id}/run             # Async execution
GET    /focus-groups/{id}/responses

# RAG
POST   /rag/upload                        # PDF/DOCX processing
POST   /rag/search                        # Hybrid search
POST   /rag/graph-query                   # Graph RAG

# Workflows
POST   /workflows                         # Utwórz workflow
GET    /workflows, /workflows/{id}        # Lista/szczegóły
PUT    /workflows/{id}                    # Update workflow
DELETE /workflows/{id}                    # Soft delete
PATCH  /workflows/{id}/canvas             # Quick save canvas
POST   /workflows/{id}/validate           # Pre-flight validation
POST   /workflows/{id}/execute            # Wykonaj workflow
GET    /workflows/{id}/executions         # Historia wykonań
GET    /workflows/templates               # Lista templates
POST   /workflows/templates/{id}/instantiate  # Utwórz z template

# Dashboard
GET    /dashboard/metrics, /dashboard/health/{project_id}
GET    /dashboard/usage                   # Token tracking
```

### Wzorzec Endpoint

```python
from fastapi import APIRouter, Depends, HTTPException
from app.db import get_db
from app.api.dependencies import get_current_user
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()

@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,                      # Request schema
    db: AsyncSession = Depends(get_db),          # DB dependency
    current_user: User = Depends(get_current_user),  # Auth
):
    """Utwórz projekt badawczy - kontener na persony, grupy, ankiety."""

    # Minimalna logika - walidacja + delegacja
    db_project = Project(
        name=project.name,
        description=project.description,
        target_demographics=project.target_demographics,
        owner_id=current_user.id,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return db_project  # Auto-serializacja przez Pydantic
```

### Dependency Injection

**Lokalizacja:** `app/api/dependencies.py`

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from app.core.security import decode_access_token

security = HTTPBearer()

async def get_current_user(
    credentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Wstrzykuje zalogowanego użytkownika.

    Flow: Token → JWT decode → DB fetch → Validate active
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    return user
```

**Kluczowe Dependencies:**
- `get_current_user` - JWT validation + user fetch
- `get_current_active_user` - Dodatkowo sprawdza is_active
- `get_project_for_user` - Authorization (ownership check)
- `get_db` - AsyncSession injection

---

## Warstwa Serwisowa

**Lokalizacja:** `app/services/` (~14,380 LOC)
**Rola:** Cała logika biznesowa, wywołania LLM, transformacje

### Organizacja Domenowa

```
app/services/
├── shared/                      # LLM clients, RAG singleton
├── personas/                    # Generacja person
│   ├── persona_orchestration.py     # Orkiestrator (Gemini Pro)
│   ├── persona_generator_langchain.py  # Generacja (Gemini Flash)
│   ├── segment_brief_service.py      # Kontekst społeczny per segment
│   ├── persona_validator.py          # Chi-kwadrat validation
│   ├── persona_needs_service.py      # JTBD analysis
│   └── persona_details_service.py    # Formatowanie szczegółów
├── focus_groups/                # Dyskusje
│   ├── focus_group_service_langchain.py  # Orkiestracja async
│   ├── discussion_summarizer.py          # AI summaries
│   └── memory_service_langchain.py       # Context retention
├── surveys/                     # Ankiety
│   └── survey_response_generator.py
├── rag/                         # RAG system
│   ├── rag_hybrid_search_service.py  # Vector + keyword + RRF
│   ├── rag_graph_service.py          # Graph RAG (Cypher)
│   ├── rag_document_service.py       # Document upload + embedding
│   └── rag_clients.py                # Neo4j connection
├── dashboard/                   # Metryki
│   ├── dashboard_orchestrator.py         # Agregacja metryk
│   ├── metrics_service.py                # Statystyki
│   ├── health_service.py                 # Health scoring
│   ├── usage_tracking_service.py         # LLM usage
│   └── quick_actions_service.py          # Export, summaries
└── maintenance/                 # Background
    └── cleanup_service.py                # Soft-delete cleanup (7d)
```

### Service Layer Pattern

**Zasada:** Endpointy są cienkie, serwisy zawierają logikę.

```python
# ❌ ZŁE - logika w endpoincie
@router.post("/personas/generate")
async def generate_personas(project_id: UUID, db: AsyncSession):
    # 200 linii logiki generacji person...
    pass

# ✅ DOBRE - delegacja do serwisu
@router.post("/personas/generate")
async def generate_personas(
    project_id: UUID,
    db: AsyncSession,
    current_user: User = Depends(get_current_user)
):
    service = PersonaOrchestrationService()
    result = await service.generate_personas(project_id, db, current_user)
    return result
```

### Przykład Serwisu - PersonaOrchestrationService

**Lokalizacja:** `app/services/personas/persona_orchestration.py`

```python
class PersonaOrchestrationService:
    """
    Orkiestracja generacji person:
    - Gemini 2.5 Pro dla głębokiej analizy RAG
    - Graph RAG dla kontekstu społeczno-demograficznego
    - Segment-based generation dla statystycznej reprezentatywności
    """

    def __init__(self):
        from config import models

        # Model z centralnego registry (config/models.yaml)
        model_config = models.get("personas", "orchestration")
        self.llm = build_chat_model(**model_config.params)
        self.rag_service = get_polish_society_rag()

    async def generate_personas(
        self,
        project_id: UUID,
        db: AsyncSession,
        user: User
    ) -> list[Persona]:
        """
        Flow:
        1. Pobierz projekt + target demographics
        2. Stwórz segmenty demograficzne
        3. Dla każdego segmentu:
           a. Graph RAG context (wskaźniki, trendy)
           b. Segment brief (900-1200 znaków)
        4. Równoległe generowanie person (Gemini Flash)
        5. Walidacja chi-kwadrat
        6. Event sourcing (PersonaEvent)
        """
        # 1. Fetch project
        project = await self._get_project(project_id, db)

        # 2. Create segments
        segments = await self._create_segments(project)

        # 3. Generate briefs per segment (with Graph RAG)
        briefs = await asyncio.gather(*[
            self._generate_segment_brief(seg) for seg in segments
        ])

        # 4. Parallel persona generation
        personas = await self._generate_personas_batch(briefs, db)

        # 5. Statistical validation
        is_valid = await self._validate_distribution(personas, project)

        # 6. Save with event sourcing
        await self._save_personas(personas, project, db)

        return personas
```

### Kluczowe Serwisy

**1. PersonaOrchestrationService**
- Orkiestracja całego procesu generacji person
- Tworzenie segmentów demograficznych
- Graph RAG context enrichment
- Równoległe generowanie z Gemini Flash
- Walidacja statystyczna (chi-kwadrat)

**2. RAGHybridSearchService**
- Dwuwarstwowe wyszukiwanie (vector + keyword + graph)
- RRF fusion (Reciprocal Rank Fusion)
- Embedding z Gemini (768D)
- Metadane: summary, key_facts, confidence

**3. FocusGroupServiceLangChain**
- Symulacja dyskusji (20 person × 4 pytania < 3 min)
- Memory management (context między pytaniami)
- Event sourcing (PersonaResponse + PersonaEvent)
- AI summaries (tematy, insighty, cytaty)

**4. DashboardOrchestrator**
- Agregacja metryk (liczba person, grup, odpowiedzi)
- Health score (0-100, diversity + quality)
- Usage tracking (tokeny, koszty, budżet)
- Quick actions (export PDF, AI summary)

**5. CleanupService**
- Hard delete soft-deleted entities po 7 dniach
- Cascade delete (Project → Personas → Events)
- Scheduled job (APScheduler, codziennie 3:00)

---

## Study Designer Chat

### Przegląd

**Study Designer Chat** to konwersacyjny system projektowania badań UX oparty na AI. Wykorzystuje **LangGraph** (state machine framework) do prowadzenia użytkownika przez wieloetapowy proces definiowania celu badania, grupy docelowej, metody badawczej i konfiguracji szczegółów. Po zebraniu informacji generuje kompletny plan badania z estymacją kosztów i czasu.

**Główne Komponenty:**
- Konwersacyjny interfejs oparty na LangGraph StateGraph
- 7 etapów przepływu: welcome → gather_goal → define_audience → select_method → configure_details → generate_plan → await_approval
- Inteligentne zadawanie pytań przez LLM (Gemini 2.5 Flash)
- Walidacja i loop-back logic (gdy odpowiedzi niejasne)
- Generacja planu w formacie Markdown z estymacjami
- Persystencja konwersacji w PostgreSQL (JSON state)

**Główne Cechy:**
- Adaptive questioning (LLM dostosowuje pytania do kontekstu)
- Structured JSON output parsing (z fallback do markdown extraction)
- Conditional routing (węzły decydują o następnym etapie)
- State persistence (pełna konwersacja zapisana w DB)
- Auto-execution po zatwierdzeniu planu

### Architektura

```
┌──────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│  StudyDesignerView → ChatInterface → MessageList + UserInput│
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTP (REST API)
                    ┌────▼────┐
                    │ API     │
                    │ Endpoints│
                    └────┬────┘
                         │
         ┌───────────────▼───────────────┐
         │   StudyDesignerOrchestrator   │
         │   (Main Service Layer)        │
         ├───────────────────────────────┤
         │ • create_session()            │
         │ • process_user_message()      │
         │ • approve_plan()              │
         │ • cancel_session()            │
         └───────┬───────────────────────┘
                 │
         ┌───────▼───────────────┐
         │ ConversationStateMachine│
         │    (LangGraph)         │
         ├────────────────────────┤
         │ StateGraph with:       │
         │ • 7 nodes              │
         │ • Conditional edges    │
         │ • Message history      │
         └───┬────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼───┐      ┌──────▼──────┐
│ NODES │      │ ROUTING     │
├───────┤      ├─────────────┤
│welcome│      │ Conditional │
│gather_│      │ logic based │
│ goal  │      │ on current_ │
│define_│      │ stage field │
│audience      └─────────────┘
│select_│
│method │
│config │
│details│
│generate
│ _plan │
│await_ │
│approval
└───┬───┘
    │
┌───▼─────────────┐
│  LLM (Gemini)   │
│  - Flash for Q&A│
│  - Temperature  │
│    0.3-0.8      │
│  - JSON output  │
└─────────────────┘
```

### Database Schema

**study_designer_sessions** - Główna tabela sesji konwersacyjnych
```sql
CREATE TABLE study_designer_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    project_id UUID REFERENCES projects(id),
    status VARCHAR(50) DEFAULT 'active',  -- active, plan_ready, approved, executing, completed, cancelled
    current_stage VARCHAR(50) DEFAULT 'welcome',  -- welcome, gather_goal, define_audience, ...
    conversation_state JSONB NOT NULL,  -- Complete LangGraph state (TypedDict serialized)
    generated_plan JSONB,  -- {markdown_summary, estimated_time_seconds, estimated_cost_usd, execution_steps}
    created_workflow_id UUID REFERENCES workflows(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Conversation State Structure (TypedDict):**
```python
{
    "session_id": "uuid-string",
    "user_id": "uuid-string",
    "messages": [
        {"role": "system"|"user"|"assistant", "content": "..."}
    ],
    "current_stage": "gather_goal",  # Controls routing
    "study_goal": "Understand checkout abandonment",  # Optional
    "target_audience": {...},  # Optional
    "research_method": "focus_group"|"personas"|"survey"|"mixed",  # Optional
    "configuration": {...},  # Optional
    "generated_plan": {...},  # Optional
    "plan_approved": false  # Optional
}
```

### LangGraph State Machine

**7 Nodes:**

1. **welcome** - Statyczna wiadomość powitalna
   - Wyświetla intro o Study Designer
   - Zawsze kieruje do `gather_goal`

2. **gather_goal** - Ekstrakcja celu badania
   - LLM analizuje odpowiedź użytkownika
   - Strukturowany output JSON: `{goal_extracted, goal, confidence, follow_up_question, assistant_message}`
   - **Loop-back:** Jeśli `goal_extracted=false` → ponowne pytanie
   - **Success:** Jeśli `goal_extracted=true` → `define_audience`

3. **define_audience** - Definicja grupy docelowej
   - Ekstrakcja demografii (wiek, płeć, lokalizacja, zawód, psychografia)
   - **Loop-back:** Jeśli demografia niepełna → doprecyzowanie
   - **Success:** Jeśli demografia OK → `select_method`

4. **select_method** - Wybór metody badawczej
   - Rekomendacja: personas / focus_group / survey / mixed
   - LLM wyjaśnia zalety/wady każdej metody
   - **Loop-back:** Jeśli wybór niejasny → wyjaśnienie opcji
   - **Success:** Jeśli metoda wybrana → `configure_details`

5. **configure_details** - Konfiguracja szczegółów
   - Zależne od metody:
     - Focus group: liczba uczestników, liczba pytań, tryb (normal/deep)
     - Personas: liczba person, segmenty demograficzne
     - Survey: typ (open-ended/rating/mixed), liczba pytań
   - **Loop-back:** Jeśli konfiguracja niepełna → doprecyzowanie
   - **Success:** Jeśli wszystko OK → `generate_plan`

6. **generate_plan** - Generacja planu badania
   - LLM generuje kompletny plan w Markdown
   - Estymacja czasu (w sekundach)
   - Estymacja kosztów (USD) - bazując na pricing.yaml
   - Execution steps (lista kroków do wykonania)
   - Zapisuje do `session.generated_plan`
   - Status sesji → `plan_ready`
   - Kieruje do → `await_approval`

7. **await_approval** - Oczekiwanie na zatwierdzenie
   - Frontend wyświetla PlanPreview z przyciskami Approve/Modify
   - **Approve:** API endpoint `/approve` → status = `approved` → trigger execution
   - **Modify:** User może wrócić do konfiguracji (TODO: nie zaimplementowane w pełni)

**Conditional Routing:**
Każdy node ustawia `current_stage` w state, a routing functions sprawdzają tę wartość:

```python
def _route_from_gather_goal(state):
    if state["current_stage"] == "define_audience":
        return "define_audience"  # Success - idź dalej
    return "gather_goal"  # Loop-back - zostań w tym node

def _route_from_define_audience(state):
    if state["current_stage"] == "select_method":
        return "select_method"
    return "define_audience"
```

### API Endpoints

**Base Path:** `/api/v1/study-designer`

1. **POST /sessions** - Utwórz nową sesję
   - Body: `{project_id?: UUID}` (optional)
   - Returns: `{session: SessionResponse}`
   - Inicjalizuje LangGraph state machine z welcome message

2. **GET /sessions/{id}** - Pobierz sesję
   - Returns: `{id, status, current_stage, messages, generated_plan?, ...}`
   - Authorization: tylko owner

3. **POST /sessions/{id}/message** - Wyślij wiadomość
   - Body: `{message: string}`
   - Returns: `{session: SessionResponse}`
   - Procesuje przez LangGraph → LLM → routing → zapisuje do DB

4. **POST /sessions/{id}/approve** - Zatwierdź plan
   - Returns: `{session: SessionResponse}`
   - Zmienia status → `approved`
   - TODO: Trigger StudyExecutor (nie zaimplementowane)

5. **DELETE /sessions/{id}** - Anuluj sesję
   - Returns: `{message: "Session cancelled successfully"}`
   - Zmienia status → `cancelled`

6. **GET /sessions** - Lista sesji użytkownika
   - Query params: `skip`, `limit`
   - Returns: `{sessions: [...], total: number}`

### Prompts (config/prompts/study_designer/)

**5 Promptów LLM (Jinja2 + YAML):**

1. **gather_goal.yaml** - Ekstrakcja celu
   - Temperature: 0.8 (creative follow-ups)
   - Output: JSON z `goal_extracted`, `goal`, `confidence`, `follow_up_question`

2. **define_audience.yaml** - Definicja demografii
   - Temperature: 0.7
   - Output: JSON z `audience_defined`, `target_audience` (age_range, demographics)

3. **select_method.yaml** - Wybór metody
   - Temperature: 0.6
   - Output: JSON z `method_selected`, `research_method`, `reasoning`

4. **configure_details.yaml** - Konfiguracja szczegółów
   - Temperature: 0.5
   - Output: JSON z `configuration_complete`, `configuration` (zależne od metody)

5. **generate_plan.yaml** - Generacja planu
   - Temperature: 0.3 (structured output)
   - Output: JSON z `markdown_summary`, `estimated_time_seconds`, `estimated_cost_usd`, `execution_steps`

### Frontend Components

**Lokalizacja:** `frontend/src/components/study-designer/`

1. **StudyDesignerView.tsx** - Landing page
   - Karta z opisem funkcji
   - Przycisk "Rozpocznij Nowe Badanie"
   - Wywołuje `createSession()` mutation

2. **ChatInterface.tsx** - Główny kontener konwersacji
   - Progress indicator (wizard steps)
   - MessageList (historia konwersacji)
   - UserInput (textarea + send button)
   - PlanPreview (gdy status = plan_ready)
   - Auto-scroll do najnowszej wiadomości

3. **MessageList.tsx** - Wyświetlanie wiadomości
   - User messages: niebieskie karty po prawej
   - Assistant messages: białe karty po lewej z markdown rendering
   - System messages: szare, wyśrodkowane
   - Loading indicator podczas oczekiwania na LLM

4. **UserInput.tsx** - Pole input
   - Textarea z auto-resize
   - Enter = send, Shift+Enter = newline
   - Disabled podczas wysyłania
   - Loading state

5. **PlanPreview.tsx** - Wyświetlanie wygenerowanego planu
   - Markdown rendering (ReactMarkdown)
   - Estymacje (czas + koszt) w grid
   - Przyciski: "Modyfikuj" i "Zatwierdź i uruchom"
   - Border + background zielony (success state)

6. **ProgressIndicator.tsx** - Wizard steps
   - 7 kroków jako horizontal stepper
   - Current step podświetlony
   - Completed steps z checkmarkiem

### TanStack Query Hooks

**Lokalizacja:** `frontend/src/hooks/useStudyDesigner.ts`

```typescript
// Query keys
const studyDesignerKeys = {
  all: ['study-designer'],
  sessions: () => [...studyDesignerKeys.all, 'sessions'],
  session: (id: string) => [...studyDesignerKeys.all, 'session', id],
};

// Queries
useSession(sessionId) - Auto-refresh co 5s jeśli aktywna
useSessions(skip, limit) - Lista sesji

// Mutations
useCreateSession() - Tworzy nową sesję
useSendMessage(sessionId) - Wysyła wiadomość
useApprovePlan(sessionId) - Zatwierdza plan
useCancelSession(sessionId) - Anuluje sesję
```

**Auto-refresh logic:**
```typescript
refetchInterval: (data) => {
  if (data?.status === 'active' || data?.status === 'plan_ready') {
    return 5000;  // Refresh co 5s
  }
  return false;  // Nie refresh dla completed/cancelled
}
```

### Testing

**Unit Tests (tests/unit/services/study_designer/):**
- `nodes/test_gather_goal.py` - Testowanie ekstrakcji celu, JSON parsing, loop-back
- `test_state_machine.py` - Routing logic, conditional edges
- `test_orchestrator.py` - Create/get/process/approve/cancel session

**Integration Tests (tests/integration/):**
- `test_study_designer_api.py` - Wszystkie 6 endpointów z prawdziwą bazą (rollback)

**Coverage Target:** 85%+

### Workflow Integration ✅

**StudyExecutor Service** (`app/services/study_designer/study_executor.py`) - Automatyczne wykonanie zatwierdzonego planu:

**Odpowiedzialności:**
1. `execute_approved_plan()` - Główna metoda wykonania:
   - Waliduje że session.status == "approved"
   - Waliduje że session.generated_plan zawiera execution_steps
   - Buduje canvas_data z execution_steps przez `_build_canvas_from_steps()`
   - Tworzy Workflow przez WorkflowService
   - Aktualizuje session: status → "executing", created_workflow_id
   - Zwraca UUID utworzonego workflow

2. `_build_canvas_from_steps()` - Generacja nodes i edges:
   - Start node (pozycja y=100)
   - Node per execution_step (vertical layout, y += 150)
   - Edges łączące nodes sekwencyjnie
   - End node (ostatni)
   - Mapowanie step types do workflow node types:
     - `personas_generation` → `personas`
     - `focus_group_discussion` → `focus_groups`
     - `survey_generation` → `surveys`
     - `ai_analysis` → `analysis`

3. `_get_node_label()` - Czytelne labels:
   - "Generate 20 Personas"
   - "Focus Group (5 questions)"
   - "AI Analysis: Themes"

4. `_generate_workflow_name()` - Nazwa workflow:
   - "Study: {study_goal}" (jeśli istnieje)
   - "Study from Session {id}" (fallback)
   - Limit 255 znaków (długi goal skracany do 200 + "...")

**Integracja z approve_plan:**

```python
# W StudyDesignerOrchestrator.approve_plan()
try:
    executor = StudyExecutor(self.db)
    workflow_id = await executor.execute_approved_plan(session, user_id)

    # Success message
    system_msg = StudyDesignerMessage(
        content=f"✅ Plan zatwierdzony! Workflow został utworzony...",
        metadata={"event": "plan_approved", "workflow_id": str(workflow_id)},
    )
except Exception as e:
    # Error handling - rollback to approved status
    session.status = "approved"
    system_msg = StudyDesignerMessage(
        content=f"⚠️ Problem podczas tworzenia workflow: {str(e)}",
        metadata={"event": "execution_failed", "error": str(e)},
    )
    raise HTTPException(500, ...) from e
```

**Flow:**
1. User zatwierdza plan (POST `/sessions/{id}/approve`)
2. Orchestrator wywołuje `StudyExecutor.execute_approved_plan()`
3. StudyExecutor parsuje execution_steps i tworzy canvas_data
4. WorkflowService zapisuje workflow w DB jako "draft"
5. Session.status → "executing", Session.created_workflow_id = workflow.id
6. Zwraca SessionResponse z created_workflow_id

**Nota:** Workflow jest tworzony jako "draft" - może być później wykonany ręcznie przez użytkownika lub automatycznie przez WorkflowExecutor (future enhancement).

**Przykładowy plan execution:**
```json
{
  "execution_steps": [
    {
      "type": "personas_generation",
      "config": {
        "num_personas": 20,
        "segments": ["25-34", "35-44"]
      }
    },
    {
      "type": "focus_group_discussion",
      "config": {
        "num_questions": 5,
        "mode": "normal"
      }
    },
    {
      "type": "ai_analysis",
      "config": {
        "analysis_type": "themes"
      }
    }
  ]
}
```

### Performance Targets

| Metryka | Target | Actual |
|---------|--------|--------|
| Session creation | < 2s | ~1.5s |
| Message processing (LLM) | < 5s | ~3-4s |
| Plan generation | < 8s | ~6s |
| Auto-refresh interval | 5s | 5s |
| DB query (get session) | < 100ms | ~50ms |

### Known Limitations

1. **Modify plan** - Przycisk "Modyfikuj" w PlanPreview robi `window.location.reload()` (temporary)
   - TODO: Wysłać wiadomość "modyfikuj {aspect}" do state machine

2. **Partial state recovery** - Jeśli sesja crashuje w trakcie node execution
   - State może być inconsistent (np. current_stage nie odpowiada messages)
   - TODO: Add state validation + recovery logic

4. **Concurrent edits** - Brak optymistic locking
   - Jeśli dwóch użytkowników edytuje tę samą sesję (edge case - każdy ma swoje sesje)
   - TODO: Add version field lub last_modified_at check

### Future Enhancements

**Priority 1:**
- [x] StudyExecutor integration (auto-execution po approve) ✅ DONE
- [ ] Modify plan flow (powrót do konfiguracji)
- [ ] Session templates (save & reuse successful configurations)
- [ ] Auto-execution workflow po utworzeniu (WorkflowExecutor integration)

**Priority 2:**
- [ ] Multi-language support (currently Polish only)
- [ ] Voice input (Web Speech API)
- [ ] Export plan to PDF/DOCX

**Priority 3:**
- [ ] Collaborative sessions (multiple users)
- [ ] AI suggestions during conversation
- [ ] Integration z RAG (context injection z past studies)

---

## Workflow System

### Przegląd

Workflow Builder to system automatyzacji procesów badawczych w Sight. Umożliwia tworzenie, walidację i wykonywanie wizualnych workflow składających się z 14 typów nodów połączonych w DAG (Directed Acyclic Graph).

**Główne Komponenty:**
- Visual Editor (React Flow canvas)
- Graph Validator (cycle detection, orphaned nodes)
- Execution Engine (topological sort, context passing)
- Template System (6 predefiniowanych workflow)
- 14 Node Types (control flow, data generation, analysis)

**Lokalizacja Kodu:**
```
Backend:
├── app/api/workflows.py                       # 11 API endpoints
├── app/models/workflow.py                     # 3 modele DB (Workflow, WorkflowExecution)
├── app/schemas/workflow.py                    # Pydantic schemas
└── app/services/workflows/                    # Service layer
    ├── workflow_service.py                    # CRUD operations
    ├── workflow_validator.py                  # Graph validation (Kahn's, BFS)
    ├── workflow_executor.py                   # Execution orchestration
    ├── workflow_template_service.py           # Template management (6 templates)
    └── node_executors/                        # Per-node execution logic
        ├── base.py                            # Abstract base executor
        ├── control_flow_executor.py           # START, END, DECISION, LOOP
        ├── data_generation_executor.py        # CREATE_PROJECT, GENERATE_PERSONAS
        ├── analysis_executor.py               # RUN_FOCUS_GROUP, ANALYZE_RESULTS
        ├── output_executor.py                 # FILTER_DATA, EXPORT_REPORT
        └── placeholder_executor.py            # MVP placeholders

Frontend:
├── frontend/src/components/workflows/         # React components
│   ├── WorkflowCanvas.tsx                     # React Flow canvas
│   ├── WorkflowSidebar.tsx                    # Node palette + properties
│   ├── PropertyPanels/                        # Per-node config panels (14 types)
│   └── TemplateGallery.tsx                    # Template selection modal
├── frontend/src/hooks/useWorkflows.ts         # API integration
└── frontend/src/types/workflow.ts             # TypeScript types
```

### Architektura

**Service Layer Pattern:**
```
┌────────────────────────────────────────────────────────────┐
│                     CLIENT (React SPA)                      │
│  WorkflowCanvas → useWorkflows hook → API calls            │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                     API ENDPOINTS (thin)                    │
│  /workflows CRUD, /validate, /execute, /templates          │
└────────────────────────────┬───────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                   SERVICE LAYER (business logic)            │
├─────────────────────────────────────────────────────────────┤
│  WorkflowService        → CRUD operations                   │
│  WorkflowValidator      → Graph validation (Kahn's, BFS)    │
│  WorkflowExecutor       → Execution orchestration           │
│  WorkflowTemplateService→ Template management               │
│  Node Executors         → Per-node execution logic          │
└────────────────────────────┬───────────────────────────────┘
                             │
            ┌────────────────┴───────────────┐
            │                                │
┌───────────▼──────────┐          ┌─────────▼──────────┐
│  DATABASE LAYER      │          │  EXTERNAL SERVICES │
├──────────────────────┤          ├────────────────────┤
│ • workflows          │          │ • LLM calls        │
│ • workflow_executions│          │ • RAG service      │
│ • Validation results │          │ • Other services   │
└──────────────────────┘          └────────────────────┘
```

**Kluczowe Zasady:**
1. **Thin Controllers:** API endpoints tylko walidują i delegują
2. **Fat Services:** Cała logika w service layer
3. **Immutable Executions:** WorkflowExecution = audit trail
4. **Graph Algorithms:** Kahn's dla topological sort, BFS dla reachability
5. **Template-First UX:** 6 prebuilt templates dla szybkiego startu

### Database Schema

**3 Główne Tabele:**

#### workflows

```sql
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- Canvas data (React Flow format)
    canvas_data JSONB NOT NULL DEFAULT '{"nodes": [], "edges": []}'::jsonb,

    -- Status management
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'archived')),
    is_template BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,  -- Soft delete

    -- Indexes
    CONSTRAINT workflows_name_not_empty CHECK (length(name) > 0)
);

CREATE INDEX idx_workflows_project_id ON workflows(project_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_owner_id ON workflows(owner_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_status ON workflows(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_is_template ON workflows(is_template) WHERE is_template = TRUE;
CREATE INDEX idx_workflows_deleted_at ON workflows(deleted_at) WHERE deleted_at IS NOT NULL;
```

**Canvas Data JSONB Structure:**
```json
{
  "nodes": [
    {
      "id": "start-1",
      "type": "start",
      "position": {"x": 100, "y": 100},
      "data": {
        "label": "Start",
        "config": {}
      }
    },
    {
      "id": "generate-personas-1",
      "type": "generate_personas",
      "position": {"x": 300, "y": 100},
      "data": {
        "label": "Generate 20 Personas",
        "config": {
          "count": 20,
          "demographic_preset": "poland_general"
        }
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "start-1",
      "target": "generate-personas-1",
      "type": "default"
    }
  ]
}
```

#### workflow_executions

```sql
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,

    -- Execution status
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),

    -- Results and errors
    result_data JSONB,           -- Final context from execution
    error_message TEXT,           -- Error details if failed

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_executions_status ON workflow_executions(status);
CREATE INDEX idx_executions_started_at ON workflow_executions(started_at DESC);
CREATE INDEX idx_executions_created_at ON workflow_executions(created_at DESC);
```

**Execution Result Data Example:**
```json
{
  "personas": [
    {"id": "uuid", "name": "Jan Kowalski", "age": 35},
    {"id": "uuid", "name": "Anna Nowak", "age": 28}
  ],
  "focus_group_result": {
    "id": "uuid",
    "summary": "Participants showed strong interest in Feature A",
    "key_insights": ["Pain point: pricing", "Opportunity: mobile app"]
  },
  "insights": {
    "themes": ["pricing", "usability", "trust"],
    "sentiment": "positive",
    "confidence": 0.87
  }
}
```

#### workflow_steps (Deprecated)

**Uwaga:** Historyczna tabela z wczesnych wersji. Obecnie nody przechowywane w `canvas_data` JSONB. Tabela pozostaje dla backward compatibility, ale nie jest aktywnie używana.

### Graph Algorithms

#### Kahn's Algorithm - Cycle Detection & Topological Sort

**Złożoność:** O(V + E) gdzie V = nodes, E = edges
**Użycie:** Walidacja DAG, określenie kolejności wykonania

**Implementacja:**
```python
def _detect_cycles_and_sort(
    nodes: list[dict],
    edges: list[dict]
) -> dict[str, Any]:
    """
    Kahn's Algorithm dla topological sort i detekcji cykli.

    Returns:
        {
            "has_cycle": bool,
            "topological_order": list[str],  # Node IDs w kolejności wykonania
            "unreachable_nodes": list[str]   # Orphaned nodes
        }
    """
    # 1. Calculate in-degree for each node
    in_degree = {node["id"]: 0 for node in nodes}
    adjacency = {node["id"]: [] for node in nodes}

    for edge in edges:
        in_degree[edge["target"]] += 1
        adjacency[edge["source"]].append(edge["target"])

    # 2. Queue nodes with in-degree 0 (starting nodes)
    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    sorted_nodes = []

    # 3. Process queue (BFS traversal)
    while queue:
        node_id = queue.pop(0)
        sorted_nodes.append(node_id)

        # Reduce in-degree for neighbors
        for neighbor in adjacency[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # 4. Check if all nodes were processed
    has_cycle = len(sorted_nodes) != len(nodes)

    # 5. Identify unreachable nodes (not in sorted_nodes)
    node_ids = {node["id"] for node in nodes}
    sorted_set = set(sorted_nodes)
    unreachable = list(node_ids - sorted_set)

    return {
        "has_cycle": has_cycle,
        "topological_order": sorted_nodes,
        "unreachable_nodes": unreachable
    }
```

**Przykład:**
```
Nodes: [A, B, C, D]
Edges: [A→B, B→C, A→D, D→C]

In-degree: {A: 0, B: 1, C: 2, D: 1}
Queue: [A]

Iteration 1: Process A → Queue: [B, D], In-degree: {B: 0, C: 2, D: 0}
Iteration 2: Process B → Queue: [D], In-degree: {C: 1, D: 0}
Iteration 3: Process D → Queue: [C], In-degree: {C: 0}
Iteration 4: Process C → Queue: []

Result: [A, B, D, C] ✅ No cycle
```

**Cycle Detection:**
```
Nodes: [A, B, C]
Edges: [A→B, B→C, C→A]

In-degree: {A: 1, B: 1, C: 1}
Queue: [] (no nodes with in-degree 0!)

Result: has_cycle = True ❌
```

#### BFS - Reachability Analysis

**Złożoność:** O(V + E)
**Użycie:** Detekcja orphaned nodes (nie połączone z START)

**Implementacja:**
```python
def _get_reachable_nodes(
    start_id: str,
    nodes: list[dict],
    edges: list[dict]
) -> set[str]:
    """
    BFS traversal od START node.

    Returns: Set node IDs osiągalnych z START
    """
    reachable = {start_id}
    queue = [start_id]

    # Build adjacency list
    adjacency = {node["id"]: [] for node in nodes}
    for edge in edges:
        adjacency[edge["source"]].append(edge["target"])

    # BFS traversal
    while queue:
        current = queue.pop(0)
        for neighbor in adjacency[current]:
            if neighbor not in reachable:
                reachable.add(neighbor)
                queue.append(neighbor)

    return reachable
```

**Przykład:**
```
Nodes: [START, A, B, C, ORPHAN]
Edges: [START→A, A→B, B→C]

Reachable from START: {START, A, B, C}
Orphaned: {ORPHAN} ❌
```

### Validation Pipeline

**WorkflowValidator Service:**

```python
class WorkflowValidator:
    """
    Graph validation pipeline:
    1. Structural checks (nodes, edges exist)
    2. START/END node checks
    3. Cycle detection (Kahn's)
    4. Reachability analysis (BFS)
    5. Node config validation
    6. Edge connection validation
    """

    async def validate_workflow(
        self,
        workflow_id: UUID,
        db: AsyncSession
    ) -> ValidationResult:
        """
        Full validation pipeline.

        Returns:
            ValidationResult(
                is_valid: bool,
                errors: list[str],
                warnings: list[str],
                graph_analysis: dict
            )
        """
        errors = []
        warnings = []

        # 1. Fetch workflow
        workflow = await self._get_workflow(workflow_id, db)
        canvas = workflow.canvas_data
        nodes = canvas.get("nodes", [])
        edges = canvas.get("edges", [])

        # 2. Structural checks
        if not nodes:
            errors.append("Workflow is empty (no nodes)")
        if not edges and len(nodes) > 1:
            warnings.append("No edges connecting nodes")

        # 3. START/END node checks
        start_nodes = [n for n in nodes if n["type"] == "start"]
        end_nodes = [n for n in nodes if n["type"] == "end"]

        if len(start_nodes) == 0:
            errors.append("Missing START node")
        elif len(start_nodes) > 1:
            warnings.append(f"Multiple START nodes detected ({len(start_nodes)})")

        if len(end_nodes) == 0:
            errors.append("Missing END node")

        # 4. Cycle detection (Kahn's Algorithm)
        graph_analysis = self._detect_cycles_and_sort(nodes, edges)

        if graph_analysis["has_cycle"]:
            errors.append("Workflow contains cycles (infinite loop detected)")

        # 5. Reachability analysis (BFS)
        if start_nodes:
            start_id = start_nodes[0]["id"]
            reachable = self._get_reachable_nodes(start_id, nodes, edges)
            orphaned = [n["id"] for n in nodes if n["id"] not in reachable]

            if orphaned:
                warnings.append(f"Orphaned nodes detected: {orphaned}")

        # 6. Node config validation
        for node in nodes:
            node_errors = self._validate_node_config(node)
            errors.extend(node_errors)

        # 7. Edge connection validation
        node_ids = {n["id"] for n in nodes}
        for edge in edges:
            if edge["source"] not in node_ids:
                errors.append(f"Edge {edge['id']} references non-existent source")
            if edge["target"] not in node_ids:
                errors.append(f"Edge {edge['id']} references non-existent target")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            graph_analysis=graph_analysis
        )
```

**Validation Response Example:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Multiple START nodes detected (2)"],
  "graph_analysis": {
    "has_cycle": false,
    "topological_order": ["start-1", "generate-1", "analyze-1", "end-1"],
    "unreachable_nodes": [],
    "node_count": 4,
    "edge_count": 3
  }
}
```

### API Endpoints

**Base Path:** `/api/v1/workflows`

#### CRUD Operations

**1. Create Workflow**
```http
POST /api/v1/workflows/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Research Workflow",
  "description": "Custom workflow for market research",
  "project_id": "uuid",
  "canvas_data": {
    "nodes": [
      {"id": "start-1", "type": "start", "position": {"x": 0, "y": 0}, "data": {}},
      {"id": "end-1", "type": "end", "position": {"x": 200, "y": 200}, "data": {}}
    ],
    "edges": [
      {"id": "e1", "source": "start-1", "target": "end-1"}
    ]
  }
}

Response: 201 Created
{
  "id": "uuid",
  "name": "My Research Workflow",
  "status": "draft",
  "is_template": false,
  "created_at": "2025-01-15T10:00:00Z",
  ...
}
```

**2. List Workflows**
```http
GET /api/v1/workflows/?project_id={uuid}&include_templates=false
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": "uuid",
    "name": "Workflow 1",
    "status": "draft",
    "node_count": 5,
    "created_at": "2025-01-15T10:00:00Z"
  }
]
```

**3. Get Workflow**
```http
GET /api/v1/workflows/{workflow_id}
Authorization: Bearer {token}

Response: 200 OK
{
  "id": "uuid",
  "name": "My Workflow",
  "canvas_data": {
    "nodes": [...],
    "edges": [...]
  },
  "status": "draft"
}
```

**4. Update Workflow**
```http
PUT /api/v1/workflows/{workflow_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated description",
  "status": "active"
}

Response: 200 OK
```

**5. Quick Save Canvas (Optimized)**
```http
PATCH /api/v1/workflows/{workflow_id}/canvas
Authorization: Bearer {token}
Content-Type: application/json

{
  "canvas_data": {
    "nodes": [...],
    "edges": [...]
  }
}

Response: 200 OK
{
  "success": true,
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**6. Delete Workflow (Soft Delete)**
```http
DELETE /api/v1/workflows/{workflow_id}
Authorization: Bearer {token}

Response: 204 No Content
```

#### Validation & Execution

**7. Validate Workflow**
```http
POST /api/v1/workflows/{workflow_id}/validate
Authorization: Bearer {token}

Response: 200 OK
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Multiple START nodes detected"],
  "graph_analysis": {
    "has_cycle": false,
    "topological_order": ["start-1", "generate-1", "end-1"]
  }
}
```

**8. Execute Workflow**
```http
POST /api/v1/workflows/{workflow_id}/execute
Authorization: Bearer {token}

Response: 201 Created
{
  "id": "execution-uuid",
  "workflow_id": "uuid",
  "status": "running",
  "started_at": "2025-01-15T10:30:00Z"
}
```

**9. Get Execution History**
```http
GET /api/v1/workflows/{workflow_id}/executions
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": "uuid",
    "status": "completed",
    "started_at": "2025-01-15T10:00:00Z",
    "completed_at": "2025-01-15T10:05:00Z",
    "result_data": {
      "personas": [...],
      "insights": {...}
    }
  }
]
```

#### Templates

**10. Get Templates**
```http
GET /api/v1/workflows/templates
Authorization: Bearer {token}

Response: 200 OK
[
  {
    "id": "basic_research",
    "name": "Basic Research",
    "description": "Quick market research with personas and survey",
    "node_count": 5,
    "estimated_time": "~30 min",
    "tags": ["research", "quick-start"],
    "canvas_data": {...}
  }
]
```

**11. Instantiate Template**
```http
POST /api/v1/workflows/templates/{template_id}/instantiate
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "uuid",
  "workflow_name": "My Custom Name"  // optional
}

Response: 201 Created
{
  "id": "workflow-uuid",
  "name": "My Custom Name",
  "canvas_data": {...}  // copied from template
}
```

### Node Types (14 Types)

#### Control Flow Nodes

**1. START**
- **Opis:** Entry point workflow
- **Konfiguracja:** Brak
- **Ograniczenia:** Dokładnie 1 per workflow
- **Output:** Empty context `{}`

**2. END**
- **Opis:** Completion marker
- **Konfiguracja:**
  ```json
  {
    "success_message": "Workflow completed successfully!"  // optional
  }
  ```
- **Output:** Final context from poprzednich nodów

**3. DECISION**
- **Opis:** Conditional branching (if/else logic)
- **Konfiguracja:**
  ```json
  {
    "condition": "persona_count > 10",  // Python expression
    "true_label": "Yes",
    "false_label": "No"
  }
  ```
- **Branches:** 2 edges (true/false)
- **Context Variables:** Dostęp do całego contextu (np. `persona_count`, `sentiment_score`)

**4. LOOP_START**
- **Opis:** Iteration start (for-each loop)
- **Konfiguracja:**
  ```json
  {
    "iteration_variable": "persona",
    "items_source": "personas",      // Key z contextu
    "max_iterations": 100
  }
  ```
- **Output:** Ustawia `{iteration_variable}` w context

**5. LOOP_END**
- **Opis:** Iteration end (jumps back to LOOP_START)
- **Konfiguracja:**
  ```json
  {
    "loop_start_node_id": "loop-start-1"
  }
  ```

#### Data Generation Nodes

**6. CREATE_PROJECT**
- **Opis:** Creates new research project
- **Konfiguracja:**
  ```json
  {
    "project_name": "New Project",
    "description": "Project for testing feature X",
    "demographic_targets": {
      "age_min": 25,
      "age_max": 45,
      "gender": ["male", "female"],
      "location": ["poland"]
    }
  }
  ```
- **Output:** `{"project_id": "uuid", "project": {...}}`
- **Integration:** `ProjectService.create_project()`

**7. GENERATE_PERSONAS**
- **Opis:** Generuje AI personas z segmentami demograficznymi
- **Konfiguracja:**
  ```json
  {
    "count": 20,
    "demographic_preset": "poland_general",
    "target_audience_description": "Tech-savvy millennials interested in fintech",
    "advanced_options": {
      "diversity_level": "medium",  // low, medium, high
      "include_edge_cases": true,
      "use_rag_context": true
    }
  }
  ```
- **Output:** `{"personas": [{"id": "uuid", "name": "...", "age": 35}, ...]}`
- **Integration:** `PersonaOrchestrationService.generate_personas()`
- **Performance:** 20 personas = ~45s

**8. CREATE_SURVEY**
- **Opis:** Tworzy ankietę dla person
- **Konfiguracja:**
  ```json
  {
    "survey_name": "Product Feedback Survey",
    "questions": [
      {
        "text": "How satisfied are you with our product?",
        "type": "scale",
        "scale_min": 1,
        "scale_max": 5
      },
      {
        "text": "What features would you like to see?",
        "type": "open_ended"
      }
    ],
    "target_personas": "all"  // or list of persona IDs
  }
  ```
- **Output:** `{"survey_id": "uuid", "survey": {...}}`
- **Integration:** `SurveyService.create_survey()` (placeholder w MVP)

#### Analysis Nodes

**9. RUN_FOCUS_GROUP**
- **Opis:** Uruchamia AI focus group discussion
- **Konfiguracja:**
  ```json
  {
    "focus_group_name": "Product Feature Discussion",
    "discussion_topics": [
      "What do you think about Feature A?",
      "How would you use this feature?",
      "What concerns do you have?"
    ],
    "num_participants": 10,
    "moderator_style": "casual"  // casual, formal, neutral
  }
  ```
- **Output:**
  ```json
  {
    "focus_group_id": "uuid",
    "responses": [...],
    "summary": "Participants showed strong interest...",
    "key_insights": ["Pain point: pricing", "Opportunity: mobile"],
    "themes": ["usability", "pricing", "trust"]
  }
  ```
- **Integration:** `FocusGroupServiceLangChain.run_discussion()`
- **Performance:** 10 personas × 3 pytania = ~2 min

**10. ANALYZE_RESULTS**
- **Opis:** Analizuje dane z poprzednich nodów
- **Konfiguracja:**
  ```json
  {
    "analysis_type": "sentiment",  // sentiment, themes, statistical
    "data_source": "survey-1",     // Node ID lub context key
    "custom_instructions": "Focus on pain points and feature requests"
  }
  ```
- **Output:**
  ```json
  {
    "analysis": {
      "sentiment": "positive",
      "confidence": 0.87,
      "key_findings": [...]
    }
  }
  ```
- **Integration:** LLM call z custom prompt

**11. GENERATE_INSIGHTS**
- **Opis:** Generuje insights z LLM
- **Konfiguracja:**
  ```json
  {
    "insight_focus": ["pain_points", "opportunities", "risks"],
    "output_format": "summary",  // summary, bullet_points, detailed
    "include_quotes": true,
    "max_insights": 10
  }
  ```
- **Output:**
  ```json
  {
    "insights": [
      {
        "title": "Pricing concerns",
        "description": "...",
        "quotes": ["..."],
        "confidence": 0.9
      }
    ]
  }
  ```

**12. COMPARE_GROUPS**
- **Opis:** Porównuje dwie grupy (A/B testing)
- **Konfiguracja:**
  ```json
  {
    "group_a_source": "focus-group-1",
    "group_b_source": "focus-group-2",
    "comparison_metrics": ["sentiment", "themes", "engagement"],
    "statistical_tests": true
  }
  ```
- **Output:**
  ```json
  {
    "comparison": {
      "group_a_sentiment": 0.75,
      "group_b_sentiment": 0.82,
      "difference": 0.07,
      "p_value": 0.03,
      "significant": true
    }
  }
  ```

#### Output Nodes

**13. FILTER_DATA**
- **Opis:** Filtruje dane według warunków
- **Konfiguracja:**
  ```json
  {
    "filter_expression": "age > 30 and satisfaction_score >= 4",
    "data_source": "personas",  // Context key
    "output_key": "filtered_personas"
  }
  ```
- **Output:** `{"filtered_personas": [...]}`

**14. EXPORT_REPORT**
- **Opis:** Eksportuje raport (PDF/DOCX/JSON/CSV)
- **Konfiguracja:**
  ```json
  {
    "report_name": "Final Research Report",
    "format": "pdf",  // pdf, docx, json, csv
    "sections": ["summary", "insights", "raw_data"],
    "include_raw_data": false,
    "template": "standard"
  }
  ```
- **Output:**
  ```json
  {
    "report_url": "https://storage.googleapis.com/.../report.pdf",
    "file_size": 1024000
  }
  ```

### Templates (6 Pre-built)

**1. basic_research**
- **Nodes:** 5 (START → GENERATE_PERSONAS → CREATE_SURVEY → ANALYZE_RESULTS → END)
- **Czas:** ~30 min
- **Use Case:** Quick market research, MVP validation
- **Output:** Personas + survey responses + basic analysis

**2. deep_dive**
- **Nodes:** 8 (START → CREATE_PROJECT → GENERATE_PERSONAS → CREATE_SURVEY → RUN_FOCUS_GROUP → ANALYZE_RESULTS → GENERATE_INSIGHTS → END)
- **Czas:** ~60 min
- **Use Case:** Comprehensive research, strategic decisions
- **Output:** Full research report z multiple data sources

**3. iterative_validation**
- **Nodes:** 7 (START → GENERATE_PERSONAS → CREATE_SURVEY → ANALYZE_RESULTS → DECISION → LOOP_START/END or END)
- **Czas:** ~45 min
- **Use Case:** Iterative hypothesis testing, continuous validation
- **Features:** Conditional looping based on confidence scores

**4. brand_perception**
- **Nodes:** 7 (START → GENERATE_PERSONAS → RUN_FOCUS_GROUP → ANALYZE_RESULTS → GENERATE_INSIGHTS → EXPORT_REPORT → END)
- **Czas:** ~40 min
- **Use Case:** Brand studies, sentiment analysis
- **Output:** Brand perception report z sentiment scores

**5. user_journey**
- **Nodes:** 6 (START → GENERATE_PERSONAS → journey_mapping → touchpoints_analysis → GENERATE_INSIGHTS → END)
- **Czas:** ~50 min
- **Use Case:** UX research, customer journey mapping
- **Output:** Journey map z pain points i opportunities

**6. feature_prioritization**
- **Nodes:** 7 (START → GENERATE_PERSONAS → features_survey → ANALYZE_RESULTS → COMPARE_GROUPS → prioritize → END)
- **Czas:** ~35 min
- **Use Case:** Product roadmap planning, feature decisions
- **Output:** Prioritized feature list z justification

### Execution Engine

**Workflow Execution Flow:**

```python
class WorkflowExecutor:
    """
    Orchestrates workflow execution:
    1. Validation
    2. Topological sort
    3. Sequential execution
    4. Context passing
    5. Error handling
    """

    async def execute_workflow(
        self,
        workflow_id: UUID,
        db: AsyncSession,
        user: User
    ) -> WorkflowExecution:
        """
        Full execution pipeline.

        Flow:
        1. Validate workflow (graph structure)
        2. Create execution record (status: pending)
        3. Get topological order (Kahn's)
        4. Execute nodes sequentially
           - Get NodeExecutor for type
           - Execute with context
           - Pass output to next nodes
        5. Update execution (status: completed/failed)
        6. Return execution with results
        """
        # 1. Validation
        validation = await self.validator.validate_workflow(workflow_id, db)
        if not validation.is_valid:
            raise ValidationError(validation.errors)

        # 2. Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status="pending",
            created_at=datetime.utcnow()
        )
        db.add(execution)
        await db.commit()

        try:
            # 3. Get workflow and topological order
            workflow = await self._get_workflow(workflow_id, db)
            nodes = workflow.canvas_data["nodes"]
            edges = workflow.canvas_data["edges"]

            graph_analysis = self.validator._detect_cycles_and_sort(nodes, edges)
            topological_order = graph_analysis["topological_order"]

            # 4. Update status to running
            execution.status = "running"
            execution.started_at = datetime.utcnow()
            await db.commit()

            # 5. Execute nodes sequentially
            context = {}  # Shared context across nodes

            for node_id in topological_order:
                node = next(n for n in nodes if n["id"] == node_id)

                # Get executor for node type
                executor = self._get_executor_for_type(node["type"])

                # Execute node
                output = await executor.execute(
                    node=node,
                    context=context,
                    db=db,
                    user=user
                )

                # Merge output into context
                context.update(output)

            # 6. Mark as completed
            execution.status = "completed"
            execution.completed_at = datetime.utcnow()
            execution.result_data = context

        except Exception as e:
            # Error handling
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.error_message = str(e)

        await db.commit()
        await db.refresh(execution)
        return execution
```

**Context Passing Example:**

```python
# Initial context
context = {}

# Node 1: GENERATE_PERSONAS
output = await personas_executor.execute(node, context, db, user)
# output = {"personas": [persona1, persona2, ...], "persona_count": 20}
context.update(output)
# context = {"personas": [...], "persona_count": 20}

# Node 2: RUN_FOCUS_GROUP (uses personas from context)
output = await focus_group_executor.execute(node, context, db, user)
# output = {"focus_group_result": {...}, "sentiment": "positive"}
context.update(output)
# context = {"personas": [...], "persona_count": 20, "focus_group_result": {...}, "sentiment": "positive"}

# Node 3: DECISION (checks condition with context)
condition = node["data"]["config"]["condition"]  # "sentiment == 'positive'"
result = eval(condition, {"sentiment": context["sentiment"]})  # True
# Executor chooses TRUE edge

# Node 4: GENERATE_INSIGHTS (uses focus_group_result from context)
output = await insights_executor.execute(node, context, db, user)
# output = {"insights": [...]}
context.update(output)

# Final context returned in WorkflowExecution.result_data
```

**Error Handling:**

```python
# Fail-fast strategy
try:
    output = await executor.execute(node, context, db, user)
except Exception as e:
    # Stop execution immediately
    execution.status = "failed"
    execution.error_message = f"Node {node['id']} failed: {str(e)}"
    execution.result_data = context  # Partial results
    await db.commit()
    raise
```

### Performance Characteristics

**Validation:**
- **Kahn's Algorithm:** O(V + E) = O(n) for typical workflows
- **BFS Reachability:** O(V + E) = O(n)
- **Total validation time:** <100ms for 50-node workflow
- **Complexity:** Linear w.r.t. number of nodes and edges

**Execution:**
- **Strategy:** Sequential (MVP) - nodes executed one by one
- **Bottleneck:** LLM calls (GENERATE_PERSONAS, RUN_FOCUS_GROUP)
- **Typical execution times:**
  - Basic Research (5 nodes): 30-60 seconds
  - Deep Dive (8 nodes): 2-5 minutes
  - Complex workflows (15+ nodes): 5-10 minutes

**Database:**
- **JSONB canvas_data:** Efficient queries, indexable
- **Indexes:** project_id, owner_id, status, deleted_at
- **Soft delete:** deleted_at timestamp (7-day retention)

**Future Optimizations:**
- Parallel execution for independent branches (DAG parallelism)
- Background tasks (Cloud Tasks) for long-running workflows
- Incremental execution (cache intermediate results)
- Real-time progress updates (WebSocket)

### Security & Authorization

**RBAC Enforcement:**

```python
# Authorization check in API layer
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession,
    current_user: User = Depends(get_current_user)
):
    """User can only access workflows in their projects."""
    workflow = await db.get(Workflow, workflow_id)

    if not workflow or workflow.deleted_at:
        raise HTTPException(404, "Workflow not found")

    # Check project ownership
    project = await db.get(Project, workflow.project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(403, "Access denied")

    return workflow
```

**Rate Limiting:**
- **Workflow execution:** 10 per hour per user (prevents abuse)
- **Workflow creation:** 100 per day per user
- **Template instantiation:** 50 per day per user

**Validation:**
- **Node configs:** Validated against Pydantic schemas
- **Edge connections:** Must reference existing nodes
- **DAG validation:** Prevents infinite loops (Kahn's algorithm)
- **Input sanitization:** Python eval() używany z restricted globals

### Testing

**Unit Tests:** 195 tests (~90% coverage)

```bash
# All workflow tests
pytest tests/unit/services/workflows/ -v

# Specific services
pytest tests/unit/services/workflows/test_workflow_service.py -v        # 39 tests
pytest tests/unit/services/workflows/test_workflow_validator.py -v      # 41 tests
pytest tests/unit/services/workflows/test_workflow_executor.py -v       # 21 tests
pytest tests/unit/services/workflows/test_node_executors.py -v          # 61 tests
pytest tests/unit/services/workflows/test_template_service.py -v        # 33 tests

# With coverage
pytest tests/unit/services/workflows/ \
  --cov=app/services/workflows \
  --cov-report=html \
  --cov-report=term-missing
```

**Test Coverage:**
- **WorkflowService:** 90%+ (CRUD operations, soft delete)
- **WorkflowValidator:** 95%+ (graph algorithms, edge cases)
- **WorkflowExecutor:** 90%+ (execution flow, error handling)
- **Node Executors:** 85%+ (per-node logic, integration)
- **TemplateService:** 90%+ (template management, instantiation)

**Key Test Cases:**
- Cycle detection (various graph topologies)
- Orphaned node detection (disconnected components)
- Topological sort correctness
- Context passing between nodes
- Error propagation and rollback
- Template instantiation with custom names
- Soft delete and recovery

### Future Enhancements

**MVP Limitations:**
1. **Synchronous execution:** Blocks HTTP request (no background tasks)
2. **Placeholder UUIDs:** Persona generation returns placeholders (parser needed)
3. **Survey service:** Not fully implemented (placeholder executor)
4. **No parallelism:** Sequential execution only
5. **Limited error recovery:** Fail-fast, no retry logic

**Roadmap (Post-MVP):**

**Phase 2: Background Execution**
- Integrate Cloud Tasks for async execution
- Real-time progress updates (WebSocket)
- Cancel/pause running workflows
- Retry failed nodes without full re-run

**Phase 3: Advanced Features**
- Parallel execution for independent branches (DAG parallelism)
- Sub-workflows (nested workflows, reusable components)
- Workflow versioning (save history, rollback)
- Conditional branches based on LLM responses
- Dynamic node creation (generate nodes at runtime)

**Phase 4: Collaboration**
- Workflow sharing (cross-project templates)
- Team permissions (view/edit/execute)
- Workflow marketplace (community templates)
- Commenting and annotations

**Phase 5: Optimization**
- Incremental execution (cache intermediate results)
- Smart caching (detect unchanged subgraphs)
- Cost optimization (reuse LLM calls)
- Performance profiling per node

### Related Documentation

**Backend:**
- `app/api/workflows.py` - API endpoint implementation
- `app/models/workflow.py` - Database models
- `app/services/workflows/` - Service layer
- `tests/unit/services/workflows/` - Test suite

**Frontend:**
- `/frontend/WORKFLOW_*.md` - React Flow integration guides
- `/frontend/src/components/workflows/` - UI components
- `/frontend/src/hooks/useWorkflows.ts` - API hooks
- `/frontend/src/types/workflow.ts` - TypeScript types

**Documentation:**
- `/docs/workflow_builder_prd.md` - Product requirements
- `/docs/workflow_design_review.md` - UX design review
- `/docs/WORKFLOW_REMAINING_PHASES.md` - Testing strategy
- `/docs/WORKFLOW_AUTO_LAYOUT.md` - Auto-layout algorithm (Dagre)
- `/docs/WORKFLOW_EXECUTION_HISTORY.md` - Execution history feature

**Migracje:**
- `alembic/versions/4bdf0d123032_add_workflows_tables.py` - Initial schema
- `alembic/versions/45c8ede416fb_extend_workflow_node_types_and_add_.py` - Node types extension

---

## RAG System

### Konfiguracja w Serwisach

Wszystkie serwisy używają scentralizowanej konfiguracji z `config/`.

```python
from config import models, prompts, rag, demographics, features

# 1. Modele LLM (z fallback chain)
model_config = models.get("personas", "generation")
llm = build_chat_model(**model_config.params)

# 2. Prompty (YAML-based, wersjonowane)
jtbd_prompt = prompts.get("personas.jtbd")
rendered = jtbd_prompt.render(age=25, occupation="Engineer")

# 3. Ustawienia RAG
chunk_size = rag.chunking.chunk_size  # 1000
use_hybrid = rag.retrieval.use_hybrid_search  # True

# 4. Feature Flags
if features.rag.enabled:
    context = rag_service.get_context(query)
```

**Migracja z app.core.config:**
```python
# STARY (deprecated, działa przez adapter)
from app.core.config import get_settings
settings = get_settings()

# NOWY (zalecany)
from config import models
model_config = models.get("personas", "generation")
```

**Zobacz:** `config/README.md` dla kompletnego przewodnika.

---

## Warstwa Danych

**Lokalizacja:** `app/models/` + `app/db/`
**Technologia:** SQLAlchemy 2.0 Async ORM + PostgreSQL + pgvector

### Modele Bazodanowe

```
app/models/
├── user.py              # Użytkownicy (auth, plan)
├── project.py           # Projekty badawcze
├── persona.py           # Syntetyczne persony
├── persona_events.py    # Event sourcing
├── focus_group.py       # Grupy fokusowe
├── survey.py            # Ankiety
├── rag_document.py      # Dokumenty RAG
└── dashboard.py         # Metryki
```

### Schemat Bazy Danych (skrócony)

**users**
- id (UUID PRIMARY KEY)
- email, password_hash, full_name
- plan (free/pro/enterprise)
- is_active, is_verified
- created_at, deleted_at (soft delete)

**projects**
- id, owner_id (FK users)
- name, description, target_demographics (JSON)
- target_sample_size
- chi_square_statistic, p_values (JSON)
- is_statistically_valid, validation_date
- created_at, updated_at, deleted_at

**personas**
- id, project_id (FK projects CASCADE)
- Demografia: age, gender, location, education_level, income_bracket, occupation
- Tożsamość: full_name, persona_title, headline, background_story
- Big Five: openness, conscientiousness, extraversion, agreeableness, neuroticism
- Hofstede: power_distance, individualism, masculinity, uncertainty_avoidance, long_term_orientation, indulgence
- Wartości: values[], interests[]
- RAG: rag_context_used, rag_citations (JSONB), rag_context_details (JSONB)
- created_at, updated_at, deleted_at

**persona_events** (Event Sourcing)
- id, persona_id (FK personas CASCADE)
- focus_group_id (FK focus_groups SET NULL)
- event_type ("response_given", "question_asked")
- event_data (JSON)
- sequence_number (unique per persona)
- embedding (VECTOR(3072)) - Gemini embedding
- timestamp

**focus_groups**
- id, project_id (FK projects CASCADE)
- name, description, questions (JSON)
- status (draft/running/completed)
- summary, key_insights (JSON)
- completed_at, created_at

**rag_documents**
- id, title, file_path, file_type
- source, metadata (JSON)
- chunks_count, embedding_model
- is_indexed, upload_date

**Pełne schematy SQL:** Zobacz `alembic/versions/` dla szczegółów.

### Wzorce Bazodanowe

#### 1. Soft Delete Pattern

```python
# Soft delete
persona.deleted_at = datetime.utcnow()
await db.commit()

# Query z wykluczeniem soft-deleted
result = await db.execute(
    select(Persona).where(
        Persona.project_id == project_id,
        Persona.deleted_at.is_(None)
    )
)

# Hard delete (cleanup job po 7 dniach)
await db.execute(
    delete(Persona).where(Persona.deleted_at < cutoff_date)
)
```

**Korzyści:** Możliwość "undo delete", audit trail, compliance (RODO).

#### 2. Event Sourcing (PersonaEvent)

```python
# Zapisz event (immutable)
event = PersonaEvent(
    persona_id=persona.id,
    event_type="response_given",
    event_data={"question": "...", "response": "...", "confidence": 0.85},
    sequence_number=next_sequence,
    embedding=embedding_vector
)
db.add(event)
await db.commit()

# Odtwórz historię
events = await db.execute(
    select(PersonaEvent)
    .where(PersonaEvent.persona_id == persona_id)
    .order_by(PersonaEvent.sequence_number)
)

# Semantic search po historii
similar_events = await db.execute(
    select(PersonaEvent)
    .order_by(PersonaEvent.embedding.cosine_distance(query_embedding))
    .limit(10)
)
```

**Korzyści:** Pełna ścieżka audytu, reprodukowalność, semantic search, debugging.

#### 3. JSON/JSONB dla Elastycznych Danych

**Użycie JSON:**
- `target_demographics` - dynamiczny schemat per projekt
- `rag_citations` - lista cytatów o zmiennej długości
- `questions` - struktury pytań (różne typy)
- `metadata` - dodatkowe dane bez fixed schema

**JSONB vs JSON:**
- JSONB dla często queryowanych (np. `rag_context_details`)
- JSON dla blob storage (np. `personality_prompt`)

#### 4. pgvector dla Embeddingów

```sql
-- Rozszerzenie
CREATE EXTENSION IF NOT EXISTS vector;

-- Kolumna
ALTER TABLE persona_events ADD COLUMN embedding VECTOR(3072);

-- Indeks IVFFlat
CREATE INDEX idx_persona_events_embedding
ON persona_events USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Wyszukiwanie
SELECT * FROM persona_events
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

### Migracje (Alembic)

```bash
# Generuj auto-migrację
alembic revision --autogenerate -m "Add field to personas"

# Zastosuj
alembic upgrade head

# Cofnij
alembic downgrade -1
```

**WAŻNE:** Alembic nie wykrywa automatycznie zmian w indeksach, custom SQL, data migrations, enum types.

---

## Wzorce Projektowe

### 1. Service Layer Pattern

**Cel:** Oddzielenie logiki biznesowej od API endpoints

```
API Endpoint (thin)          Service Layer (fat)          Data Layer
- Request validation    →    - LLM calls             →    - ORM models
- Authentication             - Database operations        - Async queries
- Response serialization     - Data transformations
```

**Korzyści:** Łatwiejsze testowanie, reużywalność, separacja odpowiedzialności.

### 2. Dependency Injection

FastAPI's `Depends()` dla wstrzykiwania dependencies:

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    credentials = Depends(security),
    db = Depends(get_db)  # Zagnieżdżone
) -> User:
    # JWT validation + DB fetch
    return user

# Użycie
@router.get("/projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    pass
```

**Korzyści:** Czytelność, automatyczne cleanup, łatwe testowanie.

### 3. Async-First Architecture

```python
# ✅ DOBRE - async throughout
async def generate_personas(project_id: UUID, db: AsyncSession):
    project = await db.execute(select(Project).where(...))

    # Parallel async LLM calls (10x szybciej)
    tasks = [generate_persona(seg) for seg in segments]
    personas = await asyncio.gather(*tasks)

    db.add_all(personas)
    await db.commit()

    return personas

# ❌ ZŁE - mixing sync and async
async def bad_example(db: AsyncSession):
    result = requests.get("https://api.example.com")  # Blokuje event loop!
    personas = db.query(Persona).all()  # Sync w async context!
```

**Korzyści:** Wysoka wydajność, równoległe przetwarzanie, lepsza skalowalność.

### 4. Event Sourcing (PersonaEvent)

Każda zmiana stanu persony to immutable event:

```python
# Zapisz event
event = PersonaEvent(
    persona_id=persona.id,
    event_type="response_given",
    event_data={...},
    sequence_number=next_seq
)

# Odtwórz stan
events = await get_persona_events(persona_id)
state = reduce(apply_event, events, initial_state)
```

**Korzyści:** Audit trail, reprodukowalność, time travel, debugging.

### 5. Centralized Configuration

**Problem:** Duplicate settings, hardcoded values, config drift.

**Rozwiązanie:** YAML-based config w `config/` (PR4 refactor).

```
config/
├── models.yaml       # LLM models (fallback chain)
├── features.yaml     # Feature flags, targets
├── app.yaml          # Infrastructure (DB, Redis)
├── prompts/          # 25+ Jinja2 templates
└── rag/              # RAG configuration
```

**Użycie:**
```python
from config import models, prompts, features

# Model z fallback
model_config = models.get("personas", "generation")
# personas.generation → personas.default → global.default

# Prompt rendering
template = prompts.get("personas.jtbd")
messages = template.render(age=25)

# Feature flags
if features.rag.enabled:
    chunk_size = features.rag.chunk_size
```

**Korzyści:** Single source of truth, type-safe, version controlled, hot reload.

---

## Kluczowe Decyzje Architektoniczne

### 1. Async-First (FastAPI + SQLAlchemy async)

**Rationale:**
- FastAPI's performance = async I/O
- Równoległe LLM calls (20 person × gather = 10x szybciej)
- Lepsza skalowalność (event loop > thread pool)
- Native PostgreSQL async support (asyncpg)

**Trade-offs:** Większa złożoność, trudniejszy debugging.

### 2. Service Layer Pattern

**Rationale:**
- Testowanie: Mock serwisów łatwiejsze niż HTTP
- Reużywalność: Ten sam serwis w API + background tasks
- SoC: API = validation/auth, Services = business logic

**Trade-offs:** Więcej plików, potencjalny over-engineering dla CRUD.

### 3. Event Sourcing dla Person

**Rationale:**
- Audit trail (compliance RODO)
- Reprodukowalność (replay events)
- Semantic search (embeddingi eventów)
- Debugging ("Dlaczego persona odpowiedziała X?")

**Trade-offs:** Więcej zapisu do DB, complexity (sequence_number).

### 4. Segment-Based Persona Generation

**Rationale:**
- Statystyczna reprezentatywność (chi-kwadrat wymaga rozkładów)
- Efektywność (batch generation = mniej LLM calls)
- Spójność (persony w segmencie mają podobny kontekst)

**Trade-offs:** Mniejsza różnorodność w segmencie.

### 5. Hybrydowy RAG (Vector + Keyword + Graph)

**Rationale:**
- **Vector:** Podobieństwo semantyczne (Gemini embeddings)
- **Keyword:** Exact matches (Neo4j full-text)
- **Graph RAG:** Strukturalna wiedza (Cypher, relationships)
- **RRF Fusion:** Łączy wyniki

**Trade-offs:** Complexity (3 systemy: PostgreSQL + Neo4j + Redis), koszty (embeddingi + LLM).

### 6. Centralized Config (config/*.yaml)

**Rationale:**
- Single source of truth (DRY)
- Version control (git history)
- Type safety (Pydantic validation)
- Fallback chains dla modeli

**Trade-offs:** Więcej plików, breaking change w PR4.

### 7. Soft Delete + Scheduled Hard Delete

**Rationale:**
- UX: "Undo delete" dla użytkowników
- Compliance: RODO wymaga permanent deletion eventually
- Performance: Hard delete w tle (nie blokuje UI)
- Audit: 7-dniowe okno dla debugowania

**Trade-offs:** Queries muszą filtrować `deleted_at.is_(None)`, storage przez 7 dni.

---

## Przepływ Requestu - Generacja Person

```
1. CLIENT REQUEST
   POST /api/v1/projects/{id}/personas/generate
   Authorization: Bearer <JWT>
   Body: {"num_personas": 20}
   ↓

2. MIDDLEWARE STACK
   RequestIDMiddleware      → request_id="abc123"
   SecurityHeadersMiddleware → Response headers
   RateLimiter              → 100 req/min check
   ↓

3. API ENDPOINT (app/api/personas/generation.py)
   - Validate request (Pydantic)
   - Get DB session (Depends)
   - Validate JWT → get_current_user
   - Check authorization (user owns project?)
   - Delegate to service
   ↓

4. SERVICE LAYER (PersonaOrchestrationService)
   a. Create demographic segments (DistributionBuilder)
   b. Generate segment briefs with Graph RAG (parallel)
   c. Generate personas per segment (Gemini Flash, parallel)
   d. Statistical validation (chi-squared test)
   e. Save to DB with event sourcing
   ↓

5. DATA LAYER
   a. RAG SERVICE
      - Graph RAG query (Neo4j Cypher)
      - Hybrid search (vector + keyword + RRF)

   b. LLM CALLS
      - Model config z config/models.yaml
      - Retry logic (tenacity, 3× exponential backoff)

   c. DATABASE
      - Batch insert personas
      - Insert events (PersonaEvent)

   d. CACHE
      - Cache segment brief (Redis, 1h TTL)
   ↓

6. RESPONSE
   HTTP 200 OK
   X-Request-ID: abc123
   {
     "personas": [...],  # 20 personas
     "validation": {
       "is_statistically_valid": true,
       "p_values": {...},
       "chi_square": {...}
     },
     "generation_time": "45.2s"
   }
```

### Timing Breakdown (20 personas)

| Etapa | Czas | Optymalizacja |
|-------|------|---------------|
| Request validation | <10ms | Pydantic |
| Authorization | ~50ms | DB + JWT |
| Create segments | <100ms | In-memory |
| Graph RAG queries | ~2s | Redis cache (1h) |
| Segment briefs (5×) | ~3s | Parallel (gather) |
| Persona generation (20×) | ~30s | Parallel batches (5 at a time) |
| Validation | ~200ms | Chi-squared |
| DB save + events | ~500ms | Batch insert |
| **TOTAL** | **~45s** | Target: <60s ✅ |

---

## Podsumowanie

### Kluczowe Cechy

1. **Async-First:** Wszystkie I/O operations non-blocking
2. **Service Layer Pattern:** Thin controllers, fat services
3. **Domain Organization:** Services per feature (personas/, rag/)
4. **Event Sourcing:** Immutable audit trail dla person
5. **Hybrydowy RAG:** Vector + keyword + graph search
6. **Centralized Config:** YAML-based, type-safe, fallback chains
7. **Soft Delete:** UX-friendly z scheduled hard delete (7d)
8. **Production-Ready:** Security headers, rate limiting, structured logging

### Zalety

- **Wydajność:** Async + parallel LLM = 10x szybciej
- **Testowalność:** Service layer łatwo mockować
- **Maintainability:** Clear separation of concerns
- **Skalowalność:** Async I/O + connection pooling
- **Bezpieczeństwo:** JWT auth, OWASP headers, rate limiting
- **Compliance:** Event sourcing + soft delete (RODO)

### Trade-offs

- **Complexity:** Async wymaga wiedzy o event loop
- **Files Count:** Service layer = więcej plików
- **Infrastructure:** Trzy bazy (PostgreSQL + Neo4j + Redis)
- **Learning Curve:** FastAPI + SQLAlchemy async + LangChain

---

**Wersja dokumentu:** 3.0 (skondensowana)
**Data:** 2025-11-03
**Źródło:** docs/architecture/backend.md (1,727 linii → 850 linii)
**Strategia:** Zachowano główne sekcje, skrócono przykłady, usunięto redundancje
