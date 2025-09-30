# Market Research SaaS Platform

AI-powered market research platform using for generating statistically representative synthetic personas, focus groups, and polarization analysis.

---

## 🚀 Quick Start (Full Stack - 1 Command)

### Prerequisites
- **Docker Desktop** (install from https://www.docker.com/products/docker-desktop/)
- **Google AI API key** (free tier available)

### Installation & Launch

```bash
# 1. Get Google AI API key
# Visit: https://ai.google.dev/gemini-api/docs/api-key

# 2. Setup environment
cp .env.example .env
# Edit .env and add: GOOGLE_API_KEY=your_key_here

# 3. Start full application (backend + frontend + databases)
./start.sh
```

**That's it!** The application will be available at:
- **🌐 Frontend UI**: http://localhost:5173
- **🔧 Backend API**: http://localhost:8000
- **📚 API Docs**: http://localhost:8000/docs

### Stop Application

```bash
docker compose down
```

---

## 🛠️ Development Setup (Without Docker)

If you want to run locally without Docker:

```bash
# 1-2. Same as above (API key + .env)

# 3. Start databases in Docker
docker compose up -d postgres redis neo4j

# 4. Install Python dependencies
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Initialize database
python scripts/init_db.py

# 6. Start backend (separate terminal)
uvicorn app.main:app --reload

# 7. Start frontend (separate terminal)
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

**Backend**: http://localhost:8000/docs
**Frontend**: http://localhost:5173

---

## 📋 Features

### Core Capabilities
- **Persona Generation**: Statistically validated synthetic personas (Big Five + Hofstede dimensions)
- **Event Sourcing**: Temporal memory with vector embeddings for consistency
- **Focus Groups**: Concurrent simulation with 100+ personas (<30s execution)
- **Polarization Detection**: K-means clustering for opinion analysis
- **Adversarial Mode**: Campaign stress testing with extreme personas

### Technology Stack
- **Backend**: FastAPI (async) + LangChain
- **LLM**: Google Gemini 2.0 Flash / Gemini 1.5 Pro (primary)
- **Embeddings**: Google Generative AI Embeddings
- **Databases**: PostgreSQL + pgvector, Redis, Neo4j
- **ML**: scikit-learn for clustering and statistics

---

## 🔑 API Keys Setup

### Google AI (Gemini) - Required

1. Visit: https://ai.google.dev/gemini-api/docs/api-key
2. Click "Get API Key"
3. Copy key (starts with `AIza...`)
4. Add to `.env`: `GOOGLE_API_KEY=your_key_here`

**Free tier**: 15 requests/minute (gemini-2.0-flash-exp)

### OpenAI / Anthropic - Optional

Set in `.env`:
```bash
OPENAI_API_KEY=sk-...        # Optional
ANTHROPIC_API_KEY=sk-ant-... # Optional
```

---

## 🎯 Available Models

Configure in `.env`:

```bash
# Gemini 2.0 Flash (default - fast + free)
DEFAULT_LLM_PROVIDER=google
DEFAULT_MODEL=gemini-2.0-flash-exp

# Gemini 1.5 Pro (more powerful)
DEFAULT_MODEL=gemini-1.5-pro

# OpenAI GPT-4
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4-turbo-preview

# Anthropic Claude
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

---

## 📊 Usage Examples

### 1. Create Project

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Product Launch Research",
    "description": "Testing new product concept",
    "target_audience": "Tech-savvy millennials"
  }'
```

### 2. Generate Personas

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/projects/{project_id}/personas/generate",
    json={
        "count": 10,
        "distribution": {
            "age_groups": {"18-24": 0.3, "25-34": 0.4, "35-44": 0.3},
            "genders": {"male": 0.5, "female": 0.5},
            "education_levels": {"bachelors": 0.6, "masters": 0.4},
            "income_brackets": {"50k-100k": 0.7, "100k+": 0.3},
            "locations": {"urban": 0.8, "suburban": 0.2}
        }
    }
)
personas = response.json()
```

### 3. Run Focus Group

```python
response = requests.post(
    "http://localhost:8000/api/v1/focus-groups",
    json={
        "project_id": project_id,
        "persona_ids": [p["id"] for p in personas],
        "questions": [
            "What's your first impression of this product?",
            "Would you buy it? Why or why not?",
            "What price seems fair?"
        ]
    }
)
```

---

## 🏗️ Project Structure

```
market-research-saas/
├── app/
│   ├── services/
│   │   ├── persona_generator_langchain.py    # LangChain + Gemini
│   │   ├── memory_service_langchain.py       # Event sourcing
│   │   ├── focus_group_service_langchain.py  # Focus groups
│   │   ├── polarization_service.py           # Clustering
│   │   └── adversarial_service.py            # Adversarial mode
│   ├── api/                 # REST endpoints
│   ├── models/              # Database models
│   ├── core/config.py       # Configuration
│   └── main.py              # FastAPI app
├── frontend/                # React + TypeScript UI
├── tests/                   # Test suite
├── .env                     # Your API keys (create this!)
├── .env.example            # Template
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Services
├── README.md               # This file
└── INSTRUKCJA_PL.md       # Polish instructions
```

---

## 🧪 Testing

### Run Tests
```bash
pytest tests/ -v
pytest --cov=app --cov-report=html
```

### Test API
```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

---

## 🎨 Frontend Setup (Optional)

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000" > .env
npm run dev
```

**Frontend**: http://localhost:5173

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Required
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=generate_with_openssl_rand_hex_32

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/market_research_db
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687

# LLM Settings
DEFAULT_LLM_PROVIDER=google
DEFAULT_MODEL=gemini-2.0-flash-exp
TEMPERATURE=0.7
MAX_TOKENS=8000
```

### Generate Secret Key
```bash
openssl rand -hex 32
```

---

## 🚨 Troubleshooting

### Database Connection Error
```bash
docker ps | grep postgres
docker compose restart postgres
docker logs market-research-postgres
```

### Invalid API Key
```bash
# Test Gemini API directly
curl -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_KEY"
```

### Port Already in Use
```bash
lsof -i :8000
kill -9 <PID>
# Or use different port
uvicorn app.main:app --port 8001
```

### Import Errors
```bash
pip install --upgrade -r requirements.txt
find . -type d -name __pycache__ -exec rm -r {} +
```

---

## 📚 API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project details

### Personas
- `POST /api/v1/projects/{id}/personas/generate` - Generate personas
- `GET /api/v1/personas/{id}` - Get persona details
- `GET /api/v1/personas/{id}/history` - Get event history

### Focus Groups
- `POST /api/v1/focus-groups` - Create focus group
- `POST /api/v1/focus-groups/{id}/run` - Execute simulation
- `GET /api/v1/focus-groups/{id}` - Get results

### Analysis
- `POST /api/v1/focus-groups/{id}/analyze-polarization` - Detect polarization
- `GET /api/v1/focus-groups/{id}/responses` - Get all responses

**Full API docs**: http://localhost:8000/docs

---

## 🎓 Key Features

### LangChain Integration
- **Prompt Templates**: Reusable, composable prompts
- **Output Parsing**: Structured JSON parsing
- **Model Flexibility**: Easy switching between providers
- **Chains**: Composable LLM workflows

### Event Sourcing
- Immutable event log for all persona interactions
- Vector embeddings for semantic retrieval
- Temporal decay for relevance weighting
- Consistency validation via LLM

### Statistical Validation
- Chi-square tests for demographic representativeness
- Automated validation (p > 0.05)
- Performance metrics (<3s per persona)

---

## 📖 Documentation

- **Polski**: [INSTRUKCJA_PL.md](INSTRUKCJA_PL.md)
- **Gemini API**: https://ai.google.dev/gemini-api/docs
- **LangChain**: https://python.langchain.com/docs/get_started/introduction

---

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

---

## 📄 License

MIT License

---

## 💡 Support

- API Documentation: http://localhost:8000/docs
- Gemini API Docs: https://ai.google.dev/gemini-api/docs
- LangChain Docs: https://python.langchain.com/

---

**Built with LangChain + Google Gemini** 🚀# Symulacja
