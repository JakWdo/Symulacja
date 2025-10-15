# sight

> Wirtualne grupy fokusowe z AI - symuluj badania rynkowe używając Google Gemini 2.5

## 🚀 Quick Start

```bash
# 1. Utwórz .env
echo "GOOGLE_API_KEY=your_gemini_api_key" > .env
echo "DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db" >> .env

# 2. Uruchom wszystko
docker-compose up -d

# 3. Migracje i indeksy
docker-compose exec api alembic upgrade head
python scripts/init_neo4j_indexes.py

# 4. Otwórz
open http://localhost:5173
```

**Dostęp:**
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474

## 📋 Co to robi?

| Feature | Opis | Czas |
|---------|------|------|
| **Persony** | AI generuje realistyczne profile (demografia + psychologia + kultura) | 30-60s / 20 person |
| **Grupy fokusowe** | Persony dyskutują o produkcie (async parallelization) | 2-5 min / 20 person |
| **Ankiety** | 4 typy pytań (choice, rating, open text) z AI odpowiedziami | <60s / 10 person |
| **Graf analizy** | Neo4j ekstraktuje koncepty, emocje, kontrowersje | 30-60s build |
| **RAG kontekst** | Hybrid search (vector + keyword) dla polskich danych | 350ms / query |

## 🏗️ Stack

```
Frontend: React 18 + TypeScript + Vite + TanStack Query + Tailwind
Backend: FastAPI + PostgreSQL (pgvector) + Redis + Neo4j
AI: Google Gemini 2.5 (Flash/Pro) via LangChain
Infra: Docker + Docker Compose
```

## 📖 Przykładowy Workflow

### 1. Utwórz projekt

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test produktu",
    "target_demographics": {
      "age_group": {"18-24": 0.3, "25-34": 0.5, "35-44": 0.2},
      "gender": {"Male": 0.5, "Female": 0.5}
    },
    "target_sample_size": 20
  }'
```

### 2. Generuj persony

```bash
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/personas/generate" \
  -H "Content-Type: application/json" \
  -d '{"num_personas": 20}'
```

**Persony zawierają:**
- Demografia: wiek, płeć, lokalizacja, edukacja, dochód, zawód
- Big Five: openness, conscientiousness, extraversion, agreeableness, neuroticism
- Hofstede: power distance, individualism, masculinity, uncertainty avoidance, long-term, indulgence
- Background story (50-150 słów)

### 3. Uruchom focus group

```bash
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/focus-groups" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sesja #1",
    "persona_ids": ["id1", "id2", ...],
    "questions": [
      "Co sądzisz o tym produkcie?",
      "Jakie funkcje są najważniejsze?",
      "Ile byłbyś skłonny zapłacić?"
    ]
  }'

curl -X POST "http://localhost:8000/api/v1/focus-groups/$FG_ID/run"
```

### 4. Pobierz insights

```bash
# AI Summary (Gemini Pro)
curl -X POST "http://localhost:8000/api/v1/focus-groups/$FG_ID/ai-summary?use_pro_model=true"

# Analiza grafowa (automatyczna)
curl "http://localhost:8000/api/v1/graph/$FG_ID/concepts"        # Kluczowe tematy
curl "http://localhost:8000/api/v1/graph/$FG_ID/controversial"  # Kontrowersje
curl "http://localhost:8000/api/v1/graph/$FG_ID/influential"    # Wpływowe persony
```

## ⚙️ Konfiguracja (.env)

```bash
# WYMAGANE
GOOGLE_API_KEY=your_gemini_api_key

# Databases
DATABASE_URL=postgresql+asyncpg://market_research:password@postgres:5432/market_research_db
REDIS_URL=redis://redis:6379/0
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=dev_password_change_in_prod

# AI Models
DEFAULT_MODEL=gemini-2.5-flash
PERSONA_GENERATION_MODEL=gemini-2.5-flash
ANALYSIS_MODEL=gemini-2.5-pro

# RAG (opcjonalne - sensowne defaulty)
RAG_USE_HYBRID_SEARCH=True
RAG_CHUNK_SIZE=1000
RAG_TOP_K=8
```

## 🧪 Testowanie

```bash
# Szybkie (domyślne: unit + integration + smoke)
pytest -v

# Z coverage
pytest -v --cov=app --cov-report=html

# Pełne (wymaga Gemini API key)
pytest -v --run-slow --run-external

# E2E smoke (bez external APIs)
pytest tests/e2e/test_e2e_ci_smoke.py -v
```

**Markery:**
- `slow` - Długie testy (domyślnie pomijane)
- `external` - Wymagają Gemini/Neo4j
- `performance` - Benchmarki (5-10 min)
- `manual` - Diagnostyka RAG

**Coverage:** 90% overall, 92% services

## 🐛 Troubleshooting

| Problem | Przyczyna | Rozwiązanie |
|---------|-----------|-------------|
| Backend nie startuje | DB down | `docker-compose restart postgres` |
| "GOOGLE_API_KEY not found" | Brak key | Dodaj do `.env` |
| Persony nie generują się | Quota exceeded | Sprawdź Google Cloud Console |
| Neo4j connection error | Indexes missing | `python scripts/init_neo4j_indexes.py` |
| Frontend "Module not found" | node_modules konflikt | `docker-compose down -v && up --build -d` |

**Nuklearna opcja (USUWA DANE!):**
```bash
docker-compose down -v
docker-compose up --build -d
docker-compose exec api alembic upgrade head
python scripts/init_neo4j_indexes.py
```

## 📚 Dokumentacja

**Główne pliki:**

| Plik | Opis | Use Case |
|------|------|----------|
| [CLAUDE.md](CLAUDE.md) | **Instrukcje dla Claude** - architektura, patterns, workflow | Deweloper pracuje z Claude |
| [docs/README.md](docs/README.md) | Indeks dokumentacji | Punkt wejścia |
| [docs/TESTING.md](docs/TESTING.md) | 380 testów - fixtures, performance | Pisanie/debug testów |
| [docs/RAG.md](docs/RAG.md) | Hybrid Search + GraphRAG | RAG troubleshooting |
| [docs/AI_ML.md](docs/AI_ML.md) | Prompts, LangChain, optimization, **segment-based architecture** | AI troubleshooting |
| [docs/DEVOPS.md](docs/DEVOPS.md) | Docker, CI/CD, monitoring | Deployment |
| [PLAN.md](PLAN.md) | Roadmap i zadania | Planowanie pracy |

## 🆕 Recent Updates

### 2025-10-15: Segment-Based Persona Architecture

**🎯 Major Refactor:** Wprowadzono segment-based architecture dla generowania person.

**Key Changes:**
- ✅ Each persona belongs to a **demographic segment** (e.g., "Młodzi Prekariusze")
- ✅ Generator **enforces demographics** from segment constraints (no random age outside bounds!)
- ✅ Each segment has **individual social context** (not global)
- ✅ UI displays **segment name** as hero header + validation alerts

**Why?** Previous architecture had mismatch: orchestration brief for "18-24 women" but generator could produce "38-year-old man". New architecture uses **structured contracts** (SegmentDefinition) to ensure consistency.

**Benefits:**
- **Consistency:** Persona ↔ segment ↔ brief zawsze pasują (HARD constraints)
- **Readability:** Mówiące nazwy segmentów ("Młodzi Prekariusze" zamiast "18-24, female, <3000 PLN")
- **Educational:** Indywidualny kontekst społeczny per segment
- **Validatable:** HARD constraints można sprawdzić (age ∈ [min, max], gender = expected)
- **Scalable:** Łatwo dodać nowe segmenty bez refactor

**See:** `docs/AI_ML.md#segment-based-persona-architecture` for technical details.

## 🛠️ Development

```bash
# Zmiana kodu Python/TypeScript → auto reload (NIE rebuild)

# Zmiana requirements.txt / package.json → rebuild
docker-compose up --build -d

# Nowa migracja DB
docker-compose exec api alembic revision --autogenerate -m "opis"
docker-compose exec api alembic upgrade head

# Logi
docker-compose logs -f api
docker-compose logs -f frontend
```

## 🎯 Architektura

### Service Layer Pattern

```
API Endpoints (app/api/*.py)
    ↓ validation, routing
Service Layer (app/services/*.py)
    ↓ business logic
Models/DB (app/models/*.py)
    ↓ data access
```

### Kluczowe Serwisy

| Serwis | Funkcja | Tech |
|--------|---------|------|
| `PersonaGeneratorLangChain` | Generuje persony z RAG + statistical sampling | Gemini Flash |
| `FocusGroupServiceLangChain` | Orkiestracja dyskusji (async parallelization) | Gemini Flash |
| `MemoryServiceLangChain` | Event sourcing z semantic search | pgvector |
| `PolishSocietyRAG` | Hybrid search (vector + keyword + RRF fusion) | Neo4j + Gemini |
| `GraphRAGService` | Graph RAG (Cypher generation, answer_question) | Neo4j + LLM |
| `RAGDocumentService` | Document ingest (chunk → embed → store) | LangChain |

### Archived Services

**app/services/archived/** - Legacy features nie używane:
- `graph_service.py` - Focus group graph analysis (concept/emotion extraction)
  - Zobacz `app/services/archived/README.md` dla instrukcji przywrócenia

## 🚀 Production Checklist

**Pre-Deploy:**
- [ ] Wszystkie 380 testów przechodzą
- [ ] Coverage >80%
- [ ] Migrations up-to-date
- [ ] Neo4j indexes utworzone
- [ ] Secrets w env vars (NIE .env!)
- [ ] CORS tylko prod domains (NIE `*`)
- [ ] DEBUG=false
- [ ] Rate limiting włączony

**Post-Deploy:**
- [ ] Smoke tests (login, personas, focus group)
- [ ] Performance (API <500ms, persona <60s, focus group <3min)
- [ ] Monitoring (error rate <1%, CPU <70%)

## 💡 Pro Tips

1. **RAG testing:** `python tests/manual/test_rag_ab_comparison.py` - porównaj konfiguracje
2. **Token optimization:** Zobacz [docs/AI_ML.md#prompt-compression](docs/AI_ML.md)
3. **Performance:** Parallel LLM calls = 3x speedup (asyncio.gather)
4. **Debug:** Czytaj logi przed pytaniem Claude - 90% problemów tam jest
5. **Backup:** `./scripts/backup.sh` przed eksperymentami z DB

## 📊 Wydajność

| Operacja | Target | Actual | Status |
|----------|--------|--------|--------|
| Persona generation (20) | <60s | 42-45s | ✅ |
| Focus group (20×4) | <3 min | 2-5 min | ✅ |
| Survey (10×10) | <60s | <45s | ✅ |
| RAG hybrid search | <350ms | 350ms | ✅ |
| Graph RAG query | <3s | 3-5s | ⚠️ |

## 🤝 Contributing

1. Przeczytaj [CLAUDE.md](CLAUDE.md) - konwencje kodu
2. Uruchom testy: `pytest tests/ -v`
3. Coverage check: `pytest --cov=app --cov-report=html`
4. Update [PLAN.md](PLAN.md) - zaznacz zrealizowane zadania

## 📝 Licencja

Projekt prywatny.

---

**Więcej:** Zobacz [docs/README.md](docs/README.md) dla szczegółowej dokumentacji technicznej.
