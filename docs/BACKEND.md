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
