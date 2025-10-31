# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Overview

**Sight** is an AI-powered virtual focus group platform that uses Google Gemini to generate realistic personas and simulate market research discussions. The system combines FastAPI backend, React frontend, and a sophisticated AI stack with RAG (Retrieval-Augmented Generation), Graph Knowledge Base (Neo4j), and vector search capabilities.

**Key Features:**
- AI-generated personas with demographic constraints
- Asynchronous AI-driven focus group discussions
- Synthetic surveys with 4 question types
- Graph analysis and concept extraction
- Hybrid search (vector + keyword with RRF fusion)
- Multi-language support (Polish/English) with i18n

---

## Quick Start Commands

### Development Environment

```bash
# Start all services (PostgreSQL, Redis, Neo4j, API, Frontend)
docker-compose up -d

# View logs
docker-compose logs -f api          # Backend logs
docker-compose logs -f frontend     # Frontend logs

# Stop services
docker-compose down

# Access interfaces
# Frontend:     http://localhost:5173
# API Docs:     http://localhost:8000/docs
# Neo4j Browser: http://localhost:7474
```

### Database Operations

```bash
# Run migrations (inside container)
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Initialize Neo4j indexes
docker-compose exec api python scripts/init_neo4j_indexes.py

# Or outside container (if Python env is set up)
python scripts/init_neo4j_indexes.py
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/integration/ -v             # Integration tests
pytest tests/e2e/ -v                     # End-to-end tests
pytest -m "not slow" -v                  # Skip slow tests

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run single test file
pytest tests/unit/services/test_persona_generator.py -v

# Run with timeout (prevents hanging tests in CI)
pytest tests/ -v --timeout=300
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Development server with hot reload
npm run dev

# Type checking + build
npm run build:check

# Build only
npm run build

# Linting
npm run lint
```

### Production Deployment

```bash
# Deploy to Google Cloud Run (via cloudbuild.yaml)
git push origin main

# Manual production build test
docker-compose -f docker-compose.prod.yml up -d

# Check production logs
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## Architecture

### Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- PostgreSQL + pgvector (relational database with vector extensions)
- Redis (caching, rate limiting)
- Neo4j (graph database for knowledge graphs)
- LangChain + Google Gemini 2.5 (AI orchestration)
- SQLAlchemy 2.0 (async ORM)
- Alembic (database migrations)

**Frontend:**
- React 18 + TypeScript
- Vite (build tool)
- TanStack Query (server state management)
- Zustand (UI state management)
- shadcn/ui + Radix UI (component library)
- Tailwind CSS (styling)
- i18next (internationalization)

**AI Stack:**
- Google Gemini Flash (fast generation)
- Google Gemini Pro (complex analysis)
- LangChain (LLM abstraction)
- LangGraph (complex workflows - optional)
- Google Gemini Embeddings (vector embeddings)

**Infrastructure:**
- Docker + Docker Compose (containerization)
- Google Cloud Run (production deployment)
- Google Cloud Build (CI/CD)
- Multi-stage Dockerfile (84% size reduction)

### Project Structure

```
sight/
├── app/                          # Backend (FastAPI)
│   ├── api/                     # REST API endpoints
│   │   ├── projects.py          # Project management
│   │   ├── personas.py          # Persona CRUD + generation
│   │   ├── focus_groups.py      # Focus group orchestration
│   │   ├── surveys.py           # Survey management
│   │   ├── analysis.py          # AI analysis endpoints
│   │   ├── rag.py               # RAG document management
│   │   ├── dashboard.py         # Dashboard metrics
│   │   ├── settings.py          # User settings + preferences
│   │   └── auth.py              # Authentication
│   ├── core/                    # Configuration & constants
│   │   ├── config.py            # Settings (Pydantic BaseSettings)
│   │   ├── security.py          # JWT, password hashing
│   │   ├── redis.py             # Redis client + utilities
│   │   ├── logging_config.py    # Structured logging
│   │   ├── constants.py         # App-wide constants
│   │   ├── demographics/        # Demographic constants (Polish + international)
│   │   └── prompts/             # LLM prompts (system, focus group, RAG)
│   ├── db/                      # Database session management
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── project.py
│   │   ├── persona.py
│   │   ├── focus_group.py
│   │   ├── survey.py
│   │   ├── dashboard.py
│   │   └── user.py
│   ├── schemas/                 # Pydantic validation schemas
│   ├── services/                # Business logic (Service Layer Pattern)
│   │   ├── shared/              # Shared utilities + LLM clients
│   │   ├── personas/            # Persona generation + orchestration
│   │   │   ├── persona_generator_langchain.py   # Main generator
│   │   │   ├── persona_orchestration_service.py # Orchestration
│   │   │   ├── persona_validator.py             # Validation
│   │   │   ├── persona_details_service.py       # Detail generation
│   │   │   ├── persona_needs_service.py         # Needs analysis
│   │   │   ├── persona_audit_service.py         # Audit logging
│   │   │   └── segment_brief_service.py         # Segment briefs
│   │   ├── focus_groups/        # Focus group services
│   │   │   ├── focus_group_service_langchain.py # Main orchestration
│   │   │   ├── discussion_summarizer.py         # AI summaries
│   │   │   └── memory_service_langchain.py      # Event sourcing + semantic search
│   │   ├── rag/                 # RAG system
│   │   │   ├── rag_document_service.py          # Document management
│   │   │   ├── graph_rag_service.py             # Graph RAG
│   │   │   └── polish_society_rag.py            # Polish context RAG
│   │   ├── surveys/             # Survey response generation
│   │   ├── dashboard/           # Dashboard metrics calculation
│   │   └── maintenance/         # Cleanup services
│   ├── middleware/              # Custom middleware
│   │   ├── security.py          # Security headers
│   │   ├── request_id.py        # Request ID tracking
│   │   └── locale.py            # i18n locale detection
│   ├── tasks/                   # Background tasks (APScheduler)
│   └── main.py                  # FastAPI app initialization
├── frontend/                     # Frontend (React + TypeScript)
│   └── src/
│       ├── components/          # React components (shadcn/ui)
│       ├── hooks/               # Custom React hooks
│       ├── lib/                 # API client + utilities
│       ├── store/               # Zustand stores
│       ├── types/               # TypeScript type definitions
│       ├── i18n/                # i18next translations
│       ├── contexts/            # React contexts (Auth)
│       └── App.tsx              # Main app component
├── tests/                        # Test suite (380+ tests)
│   ├── unit/                    # ~240 tests, <90s
│   ├── integration/             # ~70 tests, 10-30s
│   ├── e2e/                     # ~5 tests, 2-5 min
│   ├── performance/             # ~3 tests, 5-10 min
│   ├── error_handling/          # ~9 tests, 5-10s
│   ├── manual/                  # Manual test scripts
│   └── fixtures/                # Shared pytest fixtures
├── alembic/                      # Database migrations
│   └── versions/                # Migration files
├── scripts/                      # Utility scripts
│   ├── init_db.py               # Database initialization
│   └── init_neo4j_indexes.py    # Neo4j index setup
├── docs/                         # Technical documentation
│   ├── README.md                # Documentation index
│   ├── INFRASTRUCTURE.md        # Docker, CI/CD, Cloud Run
│   ├── TESTING.md               # Test suite details
│   ├── RAG.md                   # RAG system architecture
│   ├── AI_ML.md                 # AI/ML system details
│   ├── SERVICES.md              # Service structure
│   └── PERSONA_DETAILS.md       # Persona Details feature
├── docker-compose.yml            # Development environment
├── docker-compose.prod.yml       # Production environment
├── Dockerfile                    # Multi-stage backend Dockerfile
├── requirements.txt              # Python dependencies (unpinned)
├── pyproject.toml                # Python tooling config (ruff)
├── cloudbuild.yaml               # Google Cloud Build CI/CD
├── PLAN.md                       # Strategic roadmap (20-30 tasks)
└── README.md                     # User-facing documentation
```

### Core Architecture Patterns

#### 1. Service Layer Pattern

All business logic is encapsulated in service classes in `app/services/`. API endpoints are thin controllers that delegate to services.

**Example:**
```python
# API endpoint (thin controller)
@router.post("/projects/{project_id}/personas/generate")
async def generate_personas(
    project_id: UUID,
    request: PersonaGenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PersonaGeneratorLangChain(db)
    personas = await service.generate_personas(project_id, request.num_personas)
    return personas

# Service (business logic)
class PersonaGeneratorLangChain:
    async def generate_personas(self, project_id: UUID, num_personas: int):
        # Complex logic: RAG retrieval, LLM generation, validation, DB writes
        ...
```

#### 2. Domain-Organized Services

Services are organized by functional domain (not by technical layer):

- `personas/` - All persona-related services
- `focus_groups/` - All focus group services
- `rag/` - All RAG services
- `surveys/` - Survey services
- `dashboard/` - Dashboard metric services

**Benefits:** Cohesion, discoverability, easier refactoring

#### 3. Async/Await Throughout

The entire backend uses async/await for I/O operations:

- FastAPI endpoints: `async def`
- SQLAlchemy: `AsyncSession`, `asyncpg` driver
- LangChain: Async methods (`ainvoke`, `ainvoke_with_retry`)
- Redis: `aioredis` (via `redis` package)
- Neo4j: Async driver

**Important:** Always use async variants. Don't mix sync/async code.

#### 4. LangChain Abstraction

All LLM interactions go through LangChain abstractions:

```python
from app.services.shared import build_chat_model

# Build model (supports Gemini, OpenAI, Anthropic)
llm = build_chat_model(
    model_name="gemini-2.0-flash",  # or "gpt-4", "claude-3-5-sonnet"
    temperature=0.7,
    timeout=60,
)

# Invoke
response = await llm.ainvoke(messages)
```

**Benefits:** Provider flexibility, unified interface, built-in retries

#### 5. Segment-Based Personas

Personas are generated in **segments** (demographic groups), not individually:

1. Project defines target demographics (age, gender, etc.)
2. System creates demographic segments (e.g., "Males 25-34")
3. Personas are generated within each segment
4. **Constraint enforcement:** Each persona MUST match its segment demographics
5. Individual social context for realism

**Why:** Ensures demographic distribution, prevents drift, improves statistical validity

#### 6. Event Sourcing (Memory Service)

Focus group discussions use event sourcing for complete audit trail:

```python
# Every action is an event
await memory_service.add_event(
    focus_group_id=fg_id,
    event_type="discussion_started",
    event_data={"question": "What do you think?"},
)

# Query events
events = await memory_service.get_events(fg_id, event_type="response")

# Semantic search over events
results = await memory_service.semantic_search(
    query="pricing feedback",
    focus_group_id=fg_id,
)
```

**Benefits:** Complete history, semantic search, time-travel debugging

---

## Development Workflow

### 1. Adding a New API Endpoint

1. **Define Pydantic schema** in `app/schemas/`
2. **Create/update service** in `app/services/<domain>/`
3. **Add API endpoint** in `app/api/`
4. **Write tests** in `tests/unit/`, `tests/integration/`
5. **Update API docs** (FastAPI auto-generates from docstrings)

**Example:**
```python
# 1. Schema (app/schemas/persona.py)
class PersonaCreateRequest(BaseModel):
    name: str
    age: int
    background: str

# 2. Service (app/services/personas/persona_service.py)
class PersonaService:
    async def create_persona(self, data: PersonaCreateRequest) -> Persona:
        # Business logic here
        ...

# 3. API endpoint (app/api/personas.py)
@router.post("/personas")
async def create_persona(
    data: PersonaCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new persona."""
    service = PersonaService(db)
    return await service.create_persona(data)

# 4. Test (tests/unit/services/test_persona_service.py)
async def test_create_persona(db_session):
    service = PersonaService(db_session)
    data = PersonaCreateRequest(name="Test", age=25, background="...")
    persona = await service.create_persona(data)
    assert persona.name == "Test"
```

### 2. Adding a New LLM Feature

1. **Create prompt** in `app/core/prompts/` (or inline)
2. **Build LLM chain** using LangChain
3. **Add retry logic** with `tenacity` or LangChain built-in
4. **Cache results** in Redis if appropriate
5. **Add structured output** using Pydantic models
6. **Write tests** with mocked LLM responses

**Example:**
```python
from app.services.shared import build_chat_model
from langchain_core.messages import SystemMessage, HumanMessage

async def analyze_sentiment(text: str) -> str:
    llm = build_chat_model(model_name="gemini-2.0-flash", temperature=0)

    messages = [
        SystemMessage(content="You are a sentiment analysis expert."),
        HumanMessage(content=f"Analyze sentiment of: {text}"),
    ]

    response = await llm.ainvoke(messages)
    return response.content
```

### 3. Database Schema Changes

1. **Update SQLAlchemy model** in `app/models/`
2. **Generate migration**: `alembic revision --autogenerate -m "description"`
3. **Review migration** in `alembic/versions/`
4. **Test migration**: `alembic upgrade head`
5. **Update Pydantic schemas** in `app/schemas/`
6. **Update tests**

**Important:** Always review auto-generated migrations. Alembic may miss:
- Index changes
- Enum changes
- Complex constraint modifications

### 4. Frontend Component Development

1. **Create component** in `frontend/src/components/`
2. **Use shadcn/ui primitives** from `components/ui/`
3. **Add i18n keys** in `frontend/src/i18n/locales/`
4. **Use TanStack Query** for API calls
5. **Add TypeScript types** in `frontend/src/types/`
6. **Test in browser** with hot reload

**Example:**
```tsx
// frontend/src/components/PersonaCard.tsx
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useTranslation } from 'react-i18next';

export function PersonaCard({ persona }: { persona: Persona }) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{persona.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{t('persona.age')}: {persona.age}</p>
        <p>{t('persona.background')}: {persona.background}</p>
      </CardContent>
    </Card>
  );
}
```

### 5. Adding i18n Translations

1. **Add keys** to both `frontend/src/i18n/locales/pl.json` and `en.json`
2. **Use `useTranslation` hook** in components
3. **Pass variables** for dynamic content
4. **Test both languages** with language switcher

**Example:**
```json
// pl.json
{
  "persona": {
    "age": "Wiek",
    "background": "Tło",
    "greeting": "Witaj, {{name}}!"
  }
}

// en.json
{
  "persona": {
    "age": "Age",
    "background": "Background",
    "greeting": "Hello, {{name}}!"
  }
}
```

```tsx
const { t } = useTranslation();
<p>{t('persona.greeting', { name: persona.name })}</p>
```

---

## Code Conventions

### Python (Backend)

- **Style Guide:** PEP 8 (enforced via `ruff`)
- **Line Length:** 240 characters (configured in `pyproject.toml`)
- **Type Hints:** Required for all function signatures
- **Docstrings:** Polish language (project convention)
- **Async:** Use `async def` for all I/O operations
- **Imports:** Absolute imports from `app.` root
- **Error Handling:** Raise `HTTPException` from FastAPI

**Example:**
```python
from app.models.persona import Persona
from app.schemas.persona import PersonaResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

async def get_persona(db: AsyncSession, persona_id: UUID) -> Persona:
    """
    Pobiera personę z bazy danych.

    Args:
        db: Async database session
        persona_id: UUID persony

    Returns:
        Persona object

    Raises:
        HTTPException: Jeśli persona nie istnieje (404)
    """
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id)
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona {persona_id} not found"
        )

    return persona
```

### TypeScript (Frontend)

- **Style Guide:** ESLint + TypeScript strict mode
- **Components:** Functional components with hooks
- **State Management:**
  - **Server state:** TanStack Query
  - **UI state:** Zustand
- **Styling:** Tailwind CSS utility classes
- **Types:** Explicit types for all props and state
- **API Calls:** Use TanStack Query hooks

**Example:**
```tsx
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { Persona } from '@/types';

interface PersonaListProps {
  projectId: string;
}

export function PersonaList({ projectId }: PersonaListProps) {
  const { data: personas, isLoading, error } = useQuery({
    queryKey: ['personas', projectId],
    queryFn: () => api.personas.list(projectId),
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {personas?.map((persona: Persona) => (
        <PersonaCard key={persona.id} persona={persona} />
      ))}
    </div>
  );
}
```

### Testing

- **Framework:** pytest + pytest-asyncio
- **Coverage Target:** 80%+ overall, 85%+ for services
- **Test Organization:**
  - `tests/unit/` - Fast, isolated tests (<5s per test)
  - `tests/integration/` - DB + API tests (10-30s)
  - `tests/e2e/` - Full workflows (2-5 min)
  - `tests/performance/` - Benchmarks (5-10 min)
- **Fixtures:** Shared in `tests/fixtures/conftest.py`
- **Markers:** `@pytest.mark.integration`, `@pytest.mark.e2e`, `@pytest.mark.slow`
- **Mocking:** Use `pytest-mock` for external services (LLM, Redis)

**Example:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_generate_persona(db_session, mock_llm):
    """Test persona generation with mocked LLM."""
    # Arrange
    mock_llm.ainvoke.return_value = MagicMock(
        content='{"name": "Jan Kowalski", "age": 30}'
    )
    service = PersonaGeneratorLangChain(db_session)

    # Act
    persona = await service.generate_single_persona(
        demographics={"age_group": "25-34", "gender": "Male"}
    )

    # Assert
    assert persona.name == "Jan Kowalski"
    assert persona.age == 30
    mock_llm.ainvoke.assert_called_once()
```

---

## Common Patterns & Best Practices

### 1. Error Handling

```python
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

async def create_project(db: AsyncSession, data: ProjectCreate):
    try:
        project = Project(**data.dict())
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Integrity error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project with this name already exists"
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Unexpected error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )
```

### 2. Redis Caching

```python
from app.core.redis import get_redis_client
import json

async def get_cached_or_compute(key: str, compute_fn, ttl: int = 3600):
    """Get from cache or compute and cache."""
    redis = await get_redis_client()

    # Try cache first
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)

    # Compute and cache
    result = await compute_fn()
    await redis.setex(key, ttl, json.dumps(result))
    return result
```

### 3. LLM with Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
)
async def generate_with_retry(llm, messages):
    """Generate with automatic retry on transient failures."""
    return await llm.ainvoke(messages)
```

### 4. Database Query Optimization

```python
from sqlalchemy.orm import selectinload

# BAD: N+1 query problem
personas = await db.execute(select(Persona))
for persona in personas:
    project = await db.execute(select(Project).where(Project.id == persona.project_id))

# GOOD: Eager loading
result = await db.execute(
    select(Persona)
    .options(selectinload(Persona.project))
    .where(Persona.project_id == project_id)
)
personas = result.scalars().all()
```

### 5. Frontend API Error Handling

```tsx
import { useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';

const mutation = useMutation({
  mutationFn: api.personas.create,
  onSuccess: () => {
    toast.success('Persona created successfully');
    queryClient.invalidateQueries(['personas']);
  },
  onError: (error) => {
    toast.error(`Failed to create persona: ${error.message}`);
  },
});
```

---

## Environment Variables

Required `.env` file for local development:

```bash
# Google Gemini API Key (required)
GOOGLE_API_KEY=your_gemini_api_key

# Embedding model
EMBEDDING_MODEL=models/gemini-embedding-001

# Database (defaults work with docker-compose)
DATABASE_URL=postgresql+asyncpg://sight:dev_password_change_in_prod@localhost:5433/sight_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your_secret_key_here

# Optional: Other LLM providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Troubleshooting

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'apscheduler'`
**Solution:** Install dependencies inside container or locally:
```bash
docker-compose exec api pip install -r requirements.txt
# or locally:
pip install -r requirements.txt
```

**Problem:** Database connection errors
**Solution:** Check PostgreSQL is running and migrations are applied:
```bash
docker-compose up postgres -d
docker-compose exec api alembic upgrade head
```

**Problem:** Neo4j connection timeouts
**Solution:** Increase timeout or check Neo4j is ready:
```bash
docker-compose logs neo4j
# Wait for "Started" message before starting API
```

**Problem:** LLM API errors (rate limits, timeouts)
**Solution:** Check API key, quotas, and retry logic. Consider using exponential backoff:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def call_llm():
    ...
```

### Frontend Issues

**Problem:** `VITE_API_URL` not set
**Solution:** Frontend defaults to `http://localhost:8000`. Set in `.env`:
```bash
VITE_API_URL=http://localhost:8000
```

**Problem:** i18n keys missing or not updating
**Solution:** Check both `pl.json` and `en.json`, restart dev server

**Problem:** Type errors in TypeScript
**Solution:** Run type check and fix errors:
```bash
cd frontend
npm run build:check
```

### Testing Issues

**Problem:** Tests fail with database errors
**Solution:** Ensure test database is clean:
```bash
pytest tests/ --create-db
```

**Problem:** Tests hang indefinitely
**Solution:** Use timeout marker or flag:
```bash
pytest tests/ --timeout=300
```

---

## Performance Guidelines

### Backend

- **Use async/await** for all I/O operations
- **Eager load relationships** to avoid N+1 queries
- **Cache expensive operations** in Redis (LLM results, computations)
- **Use connection pooling** for PostgreSQL, Neo4j, Redis
- **Batch operations** where possible (bulk inserts, parallel LLM calls)
- **Index database columns** used in WHERE clauses

### Frontend

- **Use TanStack Query** for automatic caching and deduplication
- **Implement pagination** for large lists
- **Lazy load components** with React.lazy()
- **Optimize images** (use WebP, lazy loading)
- **Debounce search inputs** to reduce API calls
- **Use React.memo** for expensive components

### LLM Optimization

- **Use Gemini Flash** for fast generation (personas, responses)
- **Use Gemini Pro** for complex analysis (summaries, insights)
- **Parallelize LLM calls** when independent (multiple personas)
- **Cache LLM results** in Redis with TTL
- **Use structured output** (JSON mode) to reduce parsing errors
- **Set timeouts** to prevent hanging requests

**Performance Targets:**
- 20 personas: <60s (currently ~45s)
- Focus group 20 personas × 4 questions: <3 min (currently ~2 min)
- API response time: <500ms (p95)

---

## Security Considerations

- **JWT tokens** for authentication (configured in `app/core/security.py`)
- **Password hashing** with bcrypt
- **Rate limiting** with SlowAPI
- **CORS configuration** in `app/main.py`
- **Security headers** via `SecurityHeadersMiddleware`
- **SQL injection protection** via SQLAlchemy (use parameterized queries)
- **Input validation** via Pydantic schemas
- **Environment secrets** never committed to git (use `.env`)

**Production checklist:**
- [ ] Change all default passwords
- [ ] Rotate `SECRET_KEY`
- [ ] Enable HTTPS (Cloud Run does this automatically)
- [ ] Set up proper CORS origins
- [ ] Enable structured logging
- [ ] Configure Redis with TLS (Upstash)
- [ ] Set resource limits (Cloud Run)
- [ ] Monitor error rates and latency

---

## Important Notes

### Language Preferences

- **Backend code:** English (variables, functions, comments when technical)
- **Backend docstrings:** Polish (project convention)
- **Frontend code:** English
- **Frontend UI:** i18n (Polish + English)
- **User-facing strings:** Always use i18n keys
- **AI prompts:** Polish for Polish context, English for general prompts

### AI Summary Language

When generating AI summaries (focus groups, insights), the system uses the **user's preferred language** stored in their settings. Check `UserSettings.preferred_language` before generating summaries:

```python
# CORRECT: Use user's preferred language
user_settings = await db.execute(
    select(UserSettings).where(UserSettings.user_id == user_id)
)
preferred_lang = user_settings.preferred_language  # "pl" or "en"

# Pass to LLM prompt
system_message = f"Generate summary in {preferred_lang}..."
```

### Backward Compatibility

The service reorganization (2025-10-20) maintains backward compatibility via aliases:

```python
# OLD (still works)
from app.services import PersonaGenerator

# NEW (preferred)
from app.services import PersonaGeneratorLangChain
```

**Rule:** Use full names in new code, but don't break existing imports.

### Database Migrations

- **Always review** auto-generated migrations
- **Test migrations** in development before production
- **Backup production DB** before running migrations
- **Handle data migrations** separately if needed

### LLM Provider Flexibility

The system supports multiple LLM providers via LangChain:

- Google Gemini (default, recommended)
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5)

**Switching providers:**
```python
# Change model_name in build_chat_model()
llm = build_chat_model(
    model_name="gpt-4",  # or "claude-3-5-sonnet-20241022"
    temperature=0.7,
)
```

**Note:** Ensure corresponding API key is set in `.env`

---

## Documentation

Full technical documentation is in `docs/`:

- **docs/README.md** - Documentation index
- **docs/INFRASTRUCTURE.md** - Docker, CI/CD, Cloud Run (all-in-one guide)
- **docs/TESTING.md** - Test suite details (380+ tests)
- **docs/RAG.md** - Hybrid Search + GraphRAG architecture
- **docs/AI_ML.md** - AI/ML system, persona generation, LangChain
- **docs/SERVICES.md** - Service structure (domain folders)
- **docs/PERSONA_DETAILS.md** - Persona Details MVP feature
- **PLAN.md** - Strategic roadmap (20-30 active tasks)
- **README.md** - User-facing quick start

**When to update docs:**
- Architecture changes → Update this file (CLAUDE.md)
- Infrastructure changes → Update docs/INFRASTRUCTURE.md
- New test categories → Update docs/TESTING.md
- RAG system changes → Update docs/RAG.md
- Strategic decisions → Update PLAN.md

---

## Contact & Support

**Issues:** Open a GitHub issue
**Documentation:** See `docs/README.md` for full index
**CI/CD:** Check `cloudbuild.yaml` for pipeline details
**Production:** Google Cloud Run deployment (automatic on `main` push)

---

**Last Updated:** 2025-10-31
**Version:** 1.0
**Test Count:** 380+
**Documentation Style:** Narrative (continuous text, not bullet lists)
