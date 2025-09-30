# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Configuration

**IMPORTANT: Model Version Requirements**
- **ALWAYS use Gemini 2.5 models**: `gemini-2.5-pro` or `gemini-2.5-flash`
- **NEVER use Gemini 2.0 models** (e.g., `gemini-2.0-flash-exp`)
- Default should be `gemini-2.5-flash` for fast, cost-effective operations
- Use `gemini-2.5-pro` for more complex reasoning tasks

This is explicitly required by the project and must be enforced across:
- [app/core/config.py](app/core/config.py) - DEFAULT_MODEL setting
- [.env.example](.env.example) - Documentation and examples
- All documentation files

## Development Commands

### Quick Start (Full Stack)
```bash
# Setup .env with GOOGLE_API_KEY
cp .env.example .env
# Edit .env: GOOGLE_API_KEY=your_key_here

# Start everything (backend + frontend + databases)
./start.sh

# Access application
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# API Docs: http://localhost:8000/docs

# Stop everything
docker compose down
```

### Development Setup (Local Without Docker)
```bash
# Start databases only
docker compose up -d postgres redis neo4j

# Python setup
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py

# Run backend (terminal 1)
uvicorn app.main:app --reload

# Run frontend (terminal 2)
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > frontend/.env
npm run dev
```

### Database Operations
```bash
# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# View logs
docker compose logs -f api
docker compose logs -f frontend
docker compose logs -f postgres
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_persona_generator.py -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run single test
pytest tests/test_persona_generator.py::test_function_name -v
```

### Code Quality
```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Type checking
mypy app/
```

### Frontend (Optional)
```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev  # http://localhost:5173
npm run build
```

## Architecture Overview

### LangChain-Based Service Architecture

The project uses **LangChain** for all LLM interactions with **Google Gemini** as the primary provider. There are two sets of services:

1. **LangChain Services** (current, preferred):
   - [app/services/persona_generator_langchain.py](app/services/persona_generator_langchain.py)
   - [app/services/memory_service_langchain.py](app/services/memory_service_langchain.py)
   - [app/services/focus_group_service_langchain.py](app/services/focus_group_service_langchain.py)

2. **Legacy Services** (older, direct API calls):
   - [app/services/persona_generator.py](app/services/persona_generator.py)
   - [app/services/memory_service.py](app/services/memory_service.py)
   - [app/services/focus_group_service.py](app/services/focus_group_service.py)

**When modifying services, always use the LangChain versions (_langchain.py files).**

### Event Sourcing Pattern

The memory system uses **event sourcing** for temporal consistency:

- **Immutable Event Log**: All persona interactions stored as events in [app/models/event.py](app/models/event.py)
- **Sequence Numbers**: Events ordered by `sequence_number` for temporal queries
- **Vector Embeddings**: Each event embedded using Google Generative AI Embeddings (`models/embedding-001`)
- **Temporal Decay**: Relevance weighting with 30-day half-life (`exp(-time_diff / 30 days)`)
- **Consistency Checking**: LLM-based validation against past events

Key methods in [memory_service_langchain.py](app/services/memory_service_langchain.py):
- `create_event()`: Append immutable event with embedding
- `retrieve_relevant_context()`: Semantic search with temporal weighting
- `check_consistency()`: LLM validation against history

### Persona Generation Pipeline

1. **Demographic Sampling**: Chi-square validated distribution sampling
2. **Psychological Profiling**: Big Five traits + Hofstede cultural dimensions
3. **LLM Generation**: Gemini creates personality via LangChain chains
4. **Statistical Validation**: Automated chi-square tests (p > 0.05 threshold)

Core chain structure in [persona_generator_langchain.py](app/services/persona_generator_langchain.py):
```python
persona_chain = persona_prompt | llm | json_parser
```

### Multi-Database Strategy

- **PostgreSQL + pgvector**: Relational data + vector similarity search
- **Redis**: Caching and Celery task queue
- **Neo4j**: Graph relationships (persona networks, influence mapping)

All databases managed via [docker-compose.yml](docker-compose.yml).

### API Layer

FastAPI async endpoints in [app/api/](app/api/):
- [projects.py](app/api/projects.py): CRUD for research projects
- [personas.py](app/api/personas.py): Persona generation and retrieval
- [focus_groups.py](app/api/focus_groups.py): Focus group simulation
- [analysis.py](app/api/analysis.py): Polarization detection and analytics

All endpoints use async SQLAlchemy sessions via `Depends(get_db)`.

### Async Execution Model

- **FastAPI**: Fully async request handling
- **SQLAlchemy 2.0**: AsyncSession with asyncpg driver
- **LangChain**: Async chains using `.ainvoke()` and `.aembed_query()`
- **Focus Groups**: Concurrent execution with `asyncio.gather()` for 100+ personas

## Key Design Patterns

### LangChain Chains

All LLM interactions use composable chains:
```python
# Prompt -> LLM -> Parser
chain = ChatPromptTemplate.from_messages(...) | llm | JsonOutputParser()
result = await chain.ainvoke({"prompt": text})
```

### Dependency Injection

Settings accessed via `get_settings()` with LRU cache:
```python
from app.core.config import get_settings
settings = get_settings()
```

### Repository Pattern

Database access through SQLAlchemy models with async sessions:
```python
async def get_project(db: AsyncSession = Depends(get_db), project_id: UUID):
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()
```

## Configuration Management

### Environment Variables

Required in [.env](.env):
```bash
# REQUIRED
GOOGLE_API_KEY=AIza...              # Get from: https://ai.google.dev/gemini-api/docs/api-key
SECRET_KEY=<openssl rand -hex 32>

# Database URLs
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/market_research_db
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687

# LLM Configuration
DEFAULT_LLM_PROVIDER=google
DEFAULT_MODEL=gemini-2.5-flash      # MUST be 2.5, not 2.0
TEMPERATURE=0.7
MAX_TOKENS=8000
```

### Settings Hierarchy

1. `.env` file (local overrides)
2. Environment variables (deployment)
3. [config.py](app/core/config.py) defaults

## Testing Strategy

### Test Database

Tests use separate test database configuration. Initialize with:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/test_db pytest
```

### Mocking LLM Calls

When testing LangChain services, mock the LLM:
```python
from unittest.mock import AsyncMock

mock_llm = AsyncMock()
mock_llm.ainvoke.return_value = {"key": "value"}
service.llm = mock_llm
```

## Performance Targets

Configured in [app/core/config.py](app/core/config.py):
- `MAX_RESPONSE_TIME_PER_PERSONA`: 3 seconds
- `MAX_FOCUS_GROUP_TIME`: 30 seconds (for 100+ personas)
- `CONSISTENCY_ERROR_THRESHOLD`: 0.05 (5% contradiction rate)
- `STATISTICAL_SIGNIFICANCE_THRESHOLD`: 0.05 (p-value for chi-square tests)

## API Endpoints Reference

**Projects**: `/api/v1/projects`
- `POST /projects` - Create
- `GET /projects` - List
- `GET /projects/{id}` - Details
- `PUT /projects/{id}` - Update
- `DELETE /projects/{id}` - Soft delete

**Personas**: `/api/v1/personas`
- `POST /projects/{id}/personas/generate` - Generate batch
- `GET /personas/{id}` - Get details
- `GET /personas/{id}/history` - Event history

**Focus Groups**: `/api/v1/focus-groups`
- `POST /focus-groups` - Create
- `POST /focus-groups/{id}/run` - Execute simulation
- `GET /focus-groups/{id}` - Results
- `POST /focus-groups/{id}/analyze-polarization` - K-means clustering

## Common Workflows

### Adding a New LLM Provider

1. Add API key to [config.py](app/core/config.py)
2. Install LangChain provider: `pip install langchain-<provider>`
3. Update service initialization in LangChain service files
4. Add provider to `.env.example` documentation

### Modifying Persona Psychology

Update prompt templates in [persona_generator_langchain.py:122-160](app/services/persona_generator_langchain.py#L122-L160). Big Five and Hofstede dimensions are sampled from normal distributions (μ=0.5, σ=0.15-0.2).

### Adding Event Types

1. Define event type in [memory_service_langchain.py](app/services/memory_service_langchain.py)
2. Update `_event_to_text()` method for proper embedding
3. Add event schema to [app/models/event.py](app/models/event.py)

### Debugging Focus Group Consistency

Check event history and consistency scores:
```bash
curl http://localhost:8000/api/v1/personas/{persona_id}/history
```

Consistency validation occurs in [memory_service_langchain.py:169-222](app/services/memory_service_langchain.py#L169-L222).

## Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Redoc**: http://localhost:8000/redoc
- **Polish Instructions**: [INSTRUKCJA_PL.md](INSTRUKCJA_PL.md)
- **Main README**: [README.md](README.md)
- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **LangChain**: https://python.langchain.com/

## Important Notes

- **Never commit `.env`** - contains API keys
- **Use async/await** throughout - this is an async codebase
- **Prefer LangChain abstractions** over direct API calls
- **Validate demographics** using chi-square tests before deployment
- **Check consistency scores** if persona behavior seems erratic
- **Use Google Generative AI Embeddings** (`models/embedding-001`), not sentence-transformers
- **Remember**: Gemini 2.5 models ONLY (never 2.0)