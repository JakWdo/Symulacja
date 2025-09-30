# Market Research SaaS - Behavioral Analytics Platform

AI-powered market research platform for generating synthetic personas with behavioral analytics and 3D visualization.

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

## 📊 API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project details
- `PUT /api/v1/projects/{id}` - Update project
- `DELETE /api/v1/projects/{id}` - Delete project

### Personas
- `POST /api/v1/projects/{id}/personas/generate` - Generate personas
- `GET /api/v1/projects/{id}/personas` - List project personas
- `GET /api/v1/personas/{id}` - Get persona details
- `GET /api/v1/personas/{id}/history` - Get event history

### Focus Groups
- `POST /api/v1/focus-groups` - Create focus group
- `POST /api/v1/focus-groups/{id}/run` - Run simulation
- `GET /api/v1/focus-groups/{id}` - Get results
- `POST /api/v1/focus-groups/{id}/analyze-polarization` - K-means clustering

Full API documentation: http://localhost:8000/docs

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

## 🔧 Common Tasks

### View Logs
```bash
docker compose logs -f api          # Backend API
docker compose logs -f frontend     # Frontend
docker compose logs -f celery_worker # Background tasks
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

## 📈 Performance Targets

- **Persona Generation**: ~2-3 seconds per persona (Gemini API)
- **Focus Group Simulation**: <30 seconds for 100 personas
- **Chi-Square Validation**: p-value > 0.05 (95% confidence)
- **Consistency Error Rate**: <5% contradiction rate

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary. All rights reserved.

## 🔗 Resources

- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **LangChain**: https://python.langchain.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **React Three Fiber**: https://docs.pmnd.rs/react-three-fiber

## 📧 Support

For issues or questions, open an issue in the GitHub repository.

---

**Built with ❤️ using FastAPI, React, and Google Gemini**
