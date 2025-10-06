# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Market Research SaaS - AI-powered virtual focus group platform using Google Gemini to generate synthetic personas and simulate market research discussions. Minimalist version focusing on core functionality.

**Tech Stack:**
- Backend: FastAPI (Python 3.11+), PostgreSQL + pgvector, Redis, Neo4j (graph DB)
- Frontend: React 18 + TypeScript, Vite, TanStack Query, Tailwind CSS
- AI: Google Gemini 2.5 (Flash/Pro) via LangChain
- Infrastructure: Docker + Docker Compose

## Development Commands

### Docker Operations (Primary Development Method)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart backend
docker-compose restart frontend

# Rebuild containers
docker-compose up --build -d

# Stop all services
docker-compose down

# Stop and remove volumes (DELETES DATA)
docker-compose down -v
```

### Database Migrations (Alembic)

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Rollback one migration
docker-compose exec api alembic downgrade -1

# View migration history
docker-compose exec api alembic history
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --tb=short

# Run specific test file
python -m pytest tests/test_persona_generator.py -v

# List all tests
python -m pytest tests/ --collect-only
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server (standalone)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint TypeScript
npm run lint
```

## Architecture Overview

### Service Layer Pattern (Backend)

The backend uses a **service-oriented architecture** where business logic is separated from API endpoints:

```
API Endpoints (app/api/*.py)
    ↓
Service Layer (app/services/*_langchain.py)
    ↓
Models/DB (app/models/*.py)
```

**Key Services:**
- `PersonaGeneratorLangChain` - Generates statistically representative personas using Gemini + statistical sampling (chi-square validation)
- `FocusGroupServiceLangChain` - Orchestrates focus group discussions, processes responses in parallel
- `MemoryServiceLangChain` - Event sourcing system with semantic search using Google embeddings
- `DiscussionSummarizerService` - AI-powered summaries using Gemini Pro
- `PersonaValidator` - Statistical validation of persona distributions

### Memory & Context System

The platform uses **event sourcing** for persona memory:
1. Every persona action/response is stored as immutable `PersonaEvent`
2. Events have embeddings (via Google Gemini) for semantic search
3. When answering questions, relevant past context is retrieved using similarity search
4. Ensures consistency across multi-question discussions

### Parallel Processing Architecture

Focus groups process persona responses **in parallel** using asyncio:
- Each persona gets its own async task
- ~20 personas × 4 questions completes in ~2-5 minutes (vs 40+ minutes sequential)
- Target: <3s per persona response, <30s total focus group time

### Database Schema

Core models:
- `Project` - Research project container
- `Persona` - Synthetic persona with demographics + psychology (Big Five, Hofstede)
- `FocusGroup` - Discussion session linking personas to questions
- `PersonaResponse` - Individual persona answers
- `PersonaEvent` - Event sourcing log with embeddings

## Configuration & Environment

**Required Environment Variables (.env):**

```bash
# Database
DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db

# AI (REQUIRED)
GOOGLE_API_KEY=your_gemini_api_key_here

# Models
PERSONA_GENERATION_MODEL=gemini-2.5-flash
ANALYSIS_MODEL=gemini-2.5-pro
DEFAULT_MODEL=gemini-2.5-flash

# Redis & Neo4j (used by services)
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=change-me
ENVIRONMENT=development
DEBUG=true
```

**Important Settings ([app/core/config.py](app/core/config.py)):**
- `TEMPERATURE=0.7` - LLM creativity (0.0-1.0)
- `MAX_TOKENS=8000` - Max response length
- `RANDOM_SEED=42` - For reproducibility
- `MAX_RESPONSE_TIME_PER_PERSONA=3` - Performance target (seconds)
- `MAX_FOCUS_GROUP_TIME=30` - Total execution target (seconds)

## API Access Points

- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:5173
- Neo4j Browser: http://localhost:7474

## Common Development Workflows

### Testing Gemini API Connection

```bash
# Check API key is set
docker-compose exec api printenv GOOGLE_API_KEY

# Test Gemini API directly
bash -c 'API_KEY=$(docker-compose exec api printenv GOOGLE_API_KEY) && curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${API_KEY}" -H "Content-Type: application/json" -d "{\"contents\":[{\"parts\":[{\"text\":\"Hi\"}]}]}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(\"✅ API works!\" if \"candidates\" in d else \"❌ Error: \" + d.get(\"error\", {}).get(\"message\", \"Unknown\"))"'
```

### Creating Test Projects via API

```bash
# Create project
PROJECT_ID=$(curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "description": "Test project", "target_demographics": {"age_group": {"18-24": 0.5, "25-34": 0.5}, "gender": {"Male": 0.5, "Female": 0.5}}, "target_sample_size": 10}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Generate personas
curl -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/personas/generate \
  -H "Content-Type: application/json" \
  -d '{"num_personas": 10, "adversarial_mode": false}'

# List personas
curl http://localhost:8000/api/v1/projects/$PROJECT_ID/personas
```

### Persona Generation Process

The persona generation uses **hybrid AI + statistical sampling**:
1. Sample demographics from target distributions (chi-square validated)
2. Sample Big Five personality traits (normal distribution around population means)
3. Sample Hofstede cultural dimensions (based on location)
4. Use Gemini to generate realistic profile narrative, background, values
5. Validate statistical fit of final cohort

**Performance:** ~30-60s for 20 personas (Gemini Flash)

## Code Style Notes

- All services use **async/await** pattern (FastAPI + SQLAlchemy async)
- LangChain abstractions used throughout (`ChatGoogleGenerativeAI`, `ChatPromptTemplate`, etc.)
- Comprehensive docstrings in Polish (existing convention)
- Type hints required for all functions
- Constants defined in [app/core/constants.py](app/core/constants.py)

## Troubleshooting

### Backend won't start
```bash
docker-compose logs backend  # Check for errors
docker-compose restart backend db
```

### Empty persona responses
Check [app/services/focus_group_service_langchain.py](app/services/focus_group_service_langchain.py) - ensure `max_tokens` is high enough for gemini-2.5 reasoning tokens (should be 2048+)

### Database connection errors
```bash
docker-compose ps  # Verify postgres is healthy
docker-compose down -v && docker-compose up -d  # Nuclear option (deletes data)
docker-compose exec api alembic upgrade head
```

### Frontend API calls failing
Check that Vite proxy is configured correctly in [frontend/vite.config.ts](frontend/vite.config.ts) - should proxy `/api` to `http://api:8000`
