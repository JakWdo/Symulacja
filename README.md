# Market Research SaaS - Behavioral Analytics Platform

AI-powered market research platform for generating synthetic personas with statistically valid behavioral analytics.

## 📚 Documentation
- **[Statistical Validity Explained](STATISTICAL_VALIDITY.md)** - Understand how we ensure your personas are representative
- **API Documentation**: Available at http://localhost:8000/docs when backend is running

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker and Docker Compose
- Google API Key (for Gemini 2.5)

### Setup & Run

1. **Clone and configure**:
```bash
git clone <repository-url>
cd market-research-saas
cp .env.example .env
```

2. **Add your Google API Key** to `.env`:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```
Get your key at: https://ai.google.dev/gemini-api/docs/api-key

3. **Start all services**:
```bash
docker compose up -d
```

4. **Access the application**:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, password: dev_password_change_in_prod)

### Verify Services

```bash
docker compose ps
```

All containers should show "healthy" or "Up" status.

## 📖 Usage

### 1. Create a Project
- Open the frontend at http://localhost:5173
- Click "Projects" in the left sidebar
- Click "Create New Project"
- Enter project details with target demographics

### 2. Generate Personas
```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/personas/generate \
  -H "Content-Type: application/json" \
  -d '{"num_personas": 10, "adversarial_mode": false}'
```

Or use the API documentation at http://localhost:8000/docs

### 3. View Results
- Personas appear in the "Personas" panel
- 3D graph visualization shows relationships
- Click personas to see detailed profiles

## 🛠️ Development Setup (Local)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Neo4j 5.15+

### Backend Setup

1. **Install dependencies**:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start databases** (Docker):
```bash
docker compose up -d postgres redis neo4j
```

3. **Initialize database**:
```bash
python scripts/init_db.py
```

4. **Run backend**:
```bash
uvicorn app.main:app --reload
```

Backend available at: http://localhost:8000

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Run development server**:
```bash
npm run dev
```

Frontend available at: http://localhost:5173

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy 2.0 (async), LangChain
- **Frontend**: React 18, TypeScript, Vite, TanStack Query, Zustand
- **LLM**: Google Gemini 2.5 (via LangChain)
- **Databases**:
  - PostgreSQL + pgvector (relational + embeddings)
  - Redis (caching, Celery)
  - Neo4j (graph relationships)

### Key Features

#### 🧠 AI-Powered Persona Generation
- **LangChain Integration**: All LLM calls through LangChain abstractions
- **Psychological Modeling**: Big Five traits + Hofstede cultural dimensions
- **Statistical Validation**: Chi-square tests for demographic accuracy
- **Default Distributions**: Auto-fills missing demographics

#### 📊 Behavioral Analytics
- **Event Sourcing**: Immutable event log for persona interactions
- **Vector Embeddings**: Google Generative AI Embeddings (models/embedding-001)
- **Temporal Decay**: 30-day half-life for relevance weighting
- **Consistency Checking**: LLM validates against historical events

#### 🎨 3D Visualization
- **React Three Fiber**: WebGL-powered 3D graph
- **Force-Directed Layout**: d3-force physics simulation
- **Performance Optimized**: React.memo, memoization, link limiting (100 max)

## 📁 Project Structure

```
market-research-saas/
├── app/                          # Backend FastAPI application
│   ├── api/                      # API endpoints
│   │   ├── projects.py           # Project CRUD
│   │   ├── personas.py           # Persona generation
│   │   ├── focus_groups.py       # Focus group simulation
│   │   └── analysis.py           # Polarization analysis
│   ├── services/                 # Business logic
│   │   ├── persona_generator_langchain.py  # LangChain persona generator
│   │   ├── memory_service_langchain.py     # Event sourcing + embeddings
│   │   └── focus_group_service_langchain.py
│   ├── models/                   # SQLAlchemy models
│   └── core/                     # Configuration, database
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── graph/            # 3D graph visualization
│   │   │   ├── panels/           # UI panels (Projects, Personas, etc.)
│   │   │   └── ui/               # Reusable UI components
│   │   ├── lib/                  # API client, utilities
│   │   ├── hooks/                # Custom React hooks
│   │   └── store/                # Zustand state management
│   └── vite.config.ts            # Vite configuration
├── tests/                        # Backend tests
├── scripts/                      # Utility scripts
│   └── init_db.py                # Database initialization
├── alembic/                      # Database migrations
├── docker-compose.yml            # Multi-service Docker setup
├── Dockerfile                    # Backend container
└── .env                          # Environment configuration
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# LLM Configuration
GOOGLE_API_KEY=your_key_here              # Required for Gemini
DEFAULT_MODEL=gemini-2.5-flash            # MUST be 2.5, not 2.0
TEMPERATURE=0.7
MAX_TOKENS=8000

# Security
SECRET_KEY=<generate_with_openssl_rand_hex_32>

# Databases (Docker)
DATABASE_URL=postgresql+asyncpg://market_research:dev_password_change_in_prod@postgres:5432/market_research_db
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# Databases (Local)
DATABASE_URL=postgresql+asyncpg://market_research:dev_password_change_in_prod@localhost:5433/market_research_db
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
```

### Critical Configuration Notes

**IMPORTANT: Model Version Requirements**
- **ALWAYS use Gemini 2.5 models**: `gemini-2.5-pro` or `gemini-2.5-flash`
- **NEVER use Gemini 2.0 models** (e.g., `gemini-2.0-flash-exp`)
- Default should be `gemini-2.5-flash` for fast, cost-effective operations
- Use `gemini-2.5-pro` for more complex reasoning tasks

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test
```bash
pytest tests/test_persona_generator.py -v
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
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

## 📊 API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project (soft)

### Personas
- `POST /api/v1/projects/{id}/personas/generate` - Generate personas
- `GET /api/v1/projects/{id}/personas` - List project personas
- `GET /api/v1/personas/{id}` - Get persona details
- `GET /api/v1/personas/{id}/history` - Get event history
- `DELETE /api/v1/personas/{id}` - Delete persona (soft)

### Focus Groups
- `POST /api/v1/projects/{project_id}/focus-groups` - Create focus group
- `POST /api/v1/focus-groups/{id}/run` - Run simulation
- `GET /api/v1/focus-groups/{id}` - Get results
- `GET /api/v1/projects/{project_id}/focus-groups` - List focus groups
- `POST /api/v1/focus-groups/{id}/analyze-polarization` - K-means clustering
- `DELETE /api/v1/focus-groups/{id}` - Delete focus group (hard)

Full API documentation: http://localhost:8000/docs

## 🐍 Testing API with Python

### Quick Test Script

A complete Python example is provided in `examples/test_api.py`. This script demonstrates the full workflow:

```bash
# Make sure backend is running
docker compose up -d

# Run the example
python examples/test_api.py
```

### Manual API Testing

```python
import requests

# Configuration
API_URL = "http://localhost:8000/api/v1"

# 1. Create a project
project = requests.post(f"{API_URL}/projects", json={
    "name": "Test Project",
    "description": "API testing",
    "target_demographics": {
        "age_group": {"18-24": 0.3, "25-34": 0.4, "35+": 0.3},
        "gender": {"male": 0.5, "female": 0.5},
        "location": {"urban": 0.6, "suburban": 0.4}
    },
    "target_sample_size": 10
}).json()

project_id = project["id"]
print(f"Created project: {project_id}")

# 2. Generate personas
response = requests.post(
    f"{API_URL}/projects/{project_id}/personas/generate",
    json={"num_personas": 10, "adversarial_mode": False}
).json()

print(f"Generating {response['num_personas']} personas...")

# 3. Wait and check personas (takes ~20-30 seconds for 10 personas)
import time
time.sleep(30)

personas = requests.get(f"{API_URL}/projects/{project_id}/personas").json()
print(f"Generated {len(personas)} personas!")

# 4. Create focus group
persona_ids = [p["id"] for p in personas[:5]]

focus_group = requests.post(
    f"{API_URL}/projects/{project_id}/focus-groups",
    json={
        "name": "Test Focus Group",
        "persona_ids": persona_ids,
        "questions": ["What do you think about our product?"],
        "mode": "normal"
    }
).json()

print(f"Created focus group: {focus_group['id']}")

# 5. Run focus group
requests.post(f"{API_URL}/focus-groups/{focus_group['id']}/run")
print("Focus group running...")
```

### Using the API Client

```python
from examples.test_api import MarketResearchAPI

# Initialize client
api = MarketResearchAPI(base_url="http://localhost:8000/api/v1")

# Create project
project = api.create_project(
    name="My Research Project",
    description="Testing the API",
    target_demographics={
        "age_group": {"18-24": 0.2, "25-34": 0.5, "35+": 0.3},
        "gender": {"male": 0.5, "female": 0.5}
    },
    target_sample_size=15
)

# Generate personas
api.generate_personas(project["id"], num_personas=15)

# Wait for generation (~45 seconds for 15 personas)
import time
time.sleep(50)

# Get personas
personas = api.list_personas(project["id"])
print(f"Generated {len(personas)} personas")

# Get detailed persona
persona_detail = api.get_persona(personas[0]["id"])
print(f"Persona: {persona_detail['age']} y/o {persona_detail['gender']}")
print(f"Values: {persona_detail['values']}")
print(f"Background: {persona_detail['background_story']}")
```

## 🔧 Database Operations

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### View Logs

```bash
docker compose logs -f api          # Backend API
docker compose logs -f frontend     # Frontend
docker compose logs -f celery_worker # Background tasks
docker compose logs -f postgres     # PostgreSQL
```

### Reset Database

```bash
docker compose down -v  # Removes volumes
docker compose up -d
```

### Rebuild Containers

```bash
docker compose build --no-cache
docker compose up -d
```

### Access Database

```bash
docker exec -it market_research_postgres psql -U market_research -d market_research_db
```

## 🐛 Troubleshooting

### White Screen in Frontend
**Cause**: Infinite React render loop in panels
**Fix**: Applied in commit `664edb3` - removed unnecessary `setProjects`/`setPersonas` calls in useEffect

### Personas Generation Fails
**Cause**: Empty demographic distributions
**Fix**: Default distributions added for education/income in `persona_generator_langchain.py:69-70`

### Docker Containers Not Starting
```bash
# Check logs
docker compose logs api
docker compose logs frontend

# Restart services
docker compose down
docker compose up -d
```

### Database Connection Issues
Ensure databases are healthy:
```bash
docker compose ps
# All should show "healthy" status

# Test database connection
docker exec market_research_postgres pg_isready
```

### Background Task Event Loop Error
**Cause**: Using background_tasks wrapper instead of asyncio.create_task
**Fix**: Applied in `focus_groups.py:74` - use `asyncio.create_task()` directly

### Persona Selection Not Working in Focus Groups
**Cause**: Store not updating with generated personas
**Fix**: Update store in `queryFn` instead of deprecated `onSuccess` callback

## 📈 Performance Targets

- **Persona Generation**: ~2-3 seconds per persona (Gemini API)
- **Focus Group Simulation**: <30 seconds for 100 personas
- **Chi-Square Validation**: p-value > 0.05 (95% confidence)
- **Consistency Error Rate**: <5% contradiction rate

Typical execution times with Gemini 2.5-flash:

| Operation | Time | Notes |
|-----------|------|-------|
| Create Project | <100ms | Instant |
| Generate 1 Persona | 2-3s | LLM call + validation |
| Generate 10 Personas | 20-30s | Sequential generation |
| Generate 50 Personas | 2-3min | Sequential generation |
| Run Focus Group (10 personas, 3 questions) | 30-60s | Parallel execution |
| Polarization Analysis | 5-10s | K-means clustering |

## 🏛️ Architecture Deep Dive

### LangChain-Based Service Architecture

The project uses **LangChain** for all LLM interactions with **Google Gemini** as the primary provider.

**LangChain Services** (active implementation):
- `app/services/persona_generator_langchain.py`
- `app/services/memory_service_langchain.py`
- `app/services/focus_group_service_langchain.py`

### Event Sourcing Pattern

The memory system uses **event sourcing** for temporal consistency:

- **Immutable Event Log**: All persona interactions stored as events in `app/models/event.py`
- **Sequence Numbers**: Events ordered by `sequence_number` for temporal queries
- **Vector Embeddings**: Each event embedded using Google Generative AI Embeddings (`models/embedding-001`)
- **Temporal Decay**: Relevance weighting with 30-day half-life (`exp(-time_diff / 30 days)`)
- **Consistency Checking**: LLM-based validation against past events

Key methods in `memory_service_langchain.py`:
- `create_event()`: Append immutable event with embedding
- `retrieve_relevant_context()`: Semantic search with temporal weighting
- `check_consistency()`: LLM validation against history

### Persona Generation Pipeline

1. **Demographic Sampling**: Chi-square validated distribution sampling
2. **Psychological Profiling**: Big Five traits + Hofstede cultural dimensions
3. **LLM Generation**: Gemini creates personality via LangChain chains
4. **Statistical Validation**: Automated chi-square tests (p > 0.05 threshold)

Core chain structure in `persona_generator_langchain.py`:
```python
persona_chain = persona_prompt | llm | json_parser
```

### Multi-Database Strategy

- **PostgreSQL + pgvector**: Relational data + vector similarity search
- **Redis**: Caching and Celery task queue
- **Neo4j**: Graph relationships (persona networks, influence mapping)

All databases managed via `docker-compose.yml`.

### API Layer

FastAPI async endpoints in `app/api/`:
- `projects.py`: CRUD for research projects
- `personas.py`: Persona generation and retrieval
- `focus_groups.py`: Focus group simulation
- `analysis.py`: Polarization detection and analytics

All endpoints use async SQLAlchemy sessions via `Depends(get_db)`.

### Async Execution Model

- **FastAPI**: Fully async request handling
- **SQLAlchemy 2.0**: AsyncSession with asyncpg driver
- **LangChain**: Async chains using `.ainvoke()` and `.aembed_query()`
- **Focus Groups**: Concurrent execution with `asyncio.gather()` for 100+ personas

## 🎯 Key Design Patterns

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

## 📚 Common Development Workflows

### Adding a New LLM Provider

1. Add API key to `app/core/config.py`
2. Install LangChain provider: `pip install langchain-<provider>`
3. Update service initialization in LangChain service files
4. Add provider to `.env.example` documentation

### Modifying Persona Psychology

Update prompt templates in `persona_generator_langchain.py:122-160`. Big Five and Hofstede dimensions are sampled from normal distributions (μ=0.5, σ=0.15-0.2).

### Adding Event Types

1. Define event type in `memory_service_langchain.py`
2. Update `_event_to_text()` method for proper embedding
3. Add event schema to `app/models/event.py`

### Debugging Focus Group Consistency

Check event history and consistency scores:
```bash
curl http://localhost:8000/api/v1/personas/{persona_id}/history
```

Consistency validation occurs in `memory_service_langchain.py:169-222`.

## ⚠️ Important Development Notes

- **Never commit `.env`** - contains API keys
- **Use async/await** throughout - this is an async codebase
- **Prefer LangChain abstractions** over direct API calls
- **Validate demographics** using chi-square tests before deployment
- **Check consistency scores** if persona behavior seems erratic
- **Use Google Generative AI Embeddings** (`models/embedding-001`), not sentence-transformers
- **Remember**: Gemini 2.5 models ONLY (never 2.0)
- **SQL Safety**: Use `.is_(True)` instead of `== True` in SQLAlchemy queries
- **Datetime**: Use `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`

## 🔗 Resources

- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **LangChain**: https://python.langchain.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **React Three Fiber**: https://docs.pmnd.rs/react-three-fiber
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **TanStack Query**: https://tanstack.com/query/latest

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary. All rights reserved.

## 📧 Support

For issues or questions, open an issue in the GitHub repository.

---

**Built with ❤️ using FastAPI, React, and Google Gemini**
