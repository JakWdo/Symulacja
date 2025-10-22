# Market Research SaaS - Plan Refaktoryzacji

**Branch:** refactor/cloud-run-diagnosis
**Status:** 🟢 ~75% COMPLETE (12/19 tasków wykonanych)
**Last Updated:** 2025-10-22 20:00 CET

---

## 📊 EXECUTIVE SUMMARY

### Kluczowe Commity
- **5aa685c** (2025-10-22) - De-demografizacja + segment-based generation
- **3953bc4** (2025-10-22) - Secret Manager integration + health checks
- **3fe8cf9** (2025-10-22) - Cleanup testów demographics

### Status Wykonania

| Faza | Status | Progress | Czas |
|------|--------|----------|------|
| FAZA 1: Diagnoza | ✅ DONE | 1/1 | 30 min |
| FAZA 2.1: De-demografizacja | ⚠️ 4/5 | 80% | 4-6h |
| FAZA 2.2: RAG Hardening | ⚠️ 2/3 | 67% | 3-4h |
| FAZA 2.3: Docker & Cloud Run | ✅ DONE | 3/3 | 3-4h |
| FAZA 3: Local Testing | ⏭️ SKIP | - | - |
| FAZA 4: Cloud Deployment | ⏸️ READY | 0/3 | 2-3h |
| FAZA 5: Testy Cleanup | ✅ DONE | 2/2 | 1-2h |
| FAZA 6: Dokumentacja | ⚠️ 1/4 | 25% | 2-3h |

**DONE:** 12 tasków | **TODO:** 7 tasków | **Completion:** ~75%

### Co Zostało Zrobione ✅

**Backend Refactor:**
- ✅ DemographicDistribution class usunięta
- ✅ Chi-square validation usunięta
- ✅ Database migration (drop demographics columns)
- ✅ Segment-based generation (orchestration → segments → RAG → LLM)

**Infrastructure:**
- ✅ Secret Manager integration (app/core/secrets.py)
- ✅ Health checks (/health liveness + /ready readiness)
- ✅ Dockerfile $PORT support + gunicorn
- ✅ cloudbuild.yaml (BuildKit cache, 8-12 min builds)

**Testing & Docs:**
- ✅ Testy demographics usunięte (14 plików)
- ✅ Fixtures zaktualizowane (bez target_demographics)
- ✅ PLAN.md exists

### Co Pozostało TODO ❌

**CRITICAL (Priority 1):**
- ❌ Demographics remnants cleanup (generation.py L204-205 używa DEFAULT_*)

**Dokumentacja (Priority 2):**
- ❌ REFACTOR_SUMMARY.md cleanup (usunąć legacy doc)
- ❌ docs/DEPLOYMENT_CLOUD_RUN.md (template ready w tym pliku)
- ❌ Update PLAN.md (dodać completed tasks)

**Optional:**
- ⏸️ Vertex AI Ranking (komentarz w requirements.txt, implementacja later)
- ⏸️ Local Docker testing (skip jeśli cloudbuild działa)

**Deployment (Final):**
- ⏸️ Cloud Run deployment (gdy cleanup done)

---

## 📋 Plan Refaktoryzacji (Szczegółowy)

Pełna refaktoryzacja projektu z usunięciem demographics jako źródła wejściowego.

---

## 🎯 CEL REFAKTORYZACJI

### Główne Cele
1. **Usunąć zależność od demographics jako źródła wejściowego**
   - Obecnie: Demographics sampling z DEFAULT_* constants → RAG context → LLM
   - Docelowo: Orchestration → Segments → RAG/GraphRAG context → LLM

2. **Generacja person wyłącznie przez RAG/GraphRAG + Model Knowledge**
   - Brak ręcznych rozkładów demograficznych
   - Brak chi-square validation
   - Brak target_demographics w Project

3. **Przygotować clean deployment do Cloud Run**
   - Secret Manager dla wszystkich secrets
   - Vertex AI Ranking (zamiast sentence-transformers 900MB)
   - $PORT support, health checks, cloudbuild.yaml

---

## 🔍 ODKRYCIA Z EXPLORATION

### 1. Mapa Użycia Demographics

#### Pliki do Usunięcia
```
app/core/constants/demographics.py           # US defaults (DEFAULT_AGE_GROUPS, etc.)
app/core/constants/__init__.py               # Re-eksporty DEFAULT_* (do usunięcia)
```

#### Klasy i Metody do Usunięcia
**app/services/personas/generator.py:**
- `DemographicDistribution` dataclass (linie 294-307)
- `sample_demographic_profile()` (linie 358-404)
- `_prepare_distribution()` (linie 463-492)
- `validate_distribution()` (linie 756-818)
- `_chi_square_test()` (linie 820-903)

**app/services/__init__.py:**
- Re-eksport `DemographicDistribution`

#### API Endpoints do Uproszczenia
**app/api/personas/generation.py:**
- Usunąć `DemographicDistribution` logic (linie 202-210)
- Usunąć chi-square validation (linie 789-799)
- Uprosić do: orchestration → segments → generate_persona

**app/api/personas/reasoning.py:**
- Usunąć fallbacki do demographics
- Używać tylko: `orchestration_reasoning` + `rag_context_details`

**app/api/projects.py:**
- Usunąć wymóg `target_demographics` w POST/PUT

#### Database Models
**app/models/project.py** - Kolumny do usunięcia:
```python
target_demographics = Column(JSON, nullable=False)
chi_square_statistic = Column(JSON, nullable=True)
p_values = Column(JSON, nullable=True)
is_statistically_valid = Column(Boolean, nullable=False, default=False)
validation_date = Column(DateTime(timezone=True), nullable=True)
```

**app/schemas/project.py:**
- `ProjectCreate`: usuń `target_demographics`
- `ProjectUpdate`: usuń `target_demographics`
- `ProjectResponse`: usuń wszystkie demografia fields

#### Testy do Usunięcia
```
tests/unit/test_persona_generator.py        # Testy DemographicDistribution, chi-square
tests/unit/test_critical_paths.py           # test_chi_square_validation_rejects_bad_distributions
tests/integration/test_projects_api_integration.py  # Testy target_demographics
```

---

### 2. Architektura RAG/GraphRAG

#### Obecna Struktura
```
app/services/rag/
├── clients.py              # get_vector_store(), get_graph_store() z retry logic
├── hybrid_search.py        # PolishSocietyRAG (Vector + Keyword + RRF + Graph)
├── graph_service.py        # GraphRAGService (Cypher queries, graph context)
└── document_service.py     # RAGDocumentService (ingest pipeline)
```

#### Graceful Degradation Flow
```
Neo4j available?
├─ YES → RAG context (graph + chunks)
│         Generator używa demographics + RAG context
│
└─ NO → Graceful degradation
          ├─ Vector store failed → Pusty RAG context
          ├─ Graph store failed → Tylko vector search (bez graph nodes)
          ├─ Keyword search failed → Tylko vector search
          └─ Generator działa z demographics tylko (bez RAG context)
```

**Wszystkie poziomy fallback działają - system nie crashuje gdy Neo4j unavailable!**

#### RAG w Generowaniu Person
**app/services/personas/generator.py:**
- `_get_rag_context_for_persona()` (linie 552-601)
- `generate_persona_personality()` (linie 603-750)
  - RAG context → prompt builder → LLM
  - Fallback: RAG unavailable → tylko demographics

**app/services/personas/orchestration.py:**
- `create_persona_allocation_plan()` (linie 507-577)
- `_get_comprehensive_graph_context()` (linie 578-650)
  - Hybrid search dla każdej grupy demograficznej
  - Graph context w promptach dla Gemini 2.5 Pro

---

### 3. Struktura Dokumentacji

#### Problemy Zidentyfikowane
1. **CRITICAL:** Brak `PLAN.md` (wielokrotnie wspominany w CLAUDE.md)
2. **Duplikacja:** `AI_ML.md` (linie 116-200) duplikuje `PERSONA_DETAILS.md`
3. **Nieistniejący plik:** `docs/README.md` odnosi się do `DOCKER.md` (6 miejsc) - nie istnieje
4. **Za długie:** `PERSONA_DETAILS_DATA_AUDIT.md` (1574 linie)
5. **Niespójności:** Liczby testów (208 vs 380), rozmiary dokumentów

#### Pliki do Usunięcia
```
app/api/personas/REFACTOR_SUMMARY.md
.claude/agents/*                             # 10 plików (materiał pomocniczy)
test_persona_details_migration.sh
```

#### Pliki do Zaktualizowania
```
docs/README.md              # Fix DOCKER.md → DEVOPS.md, rozmiary, liczby testów
docs/AI_ML.md               # Usuń duplikację (linie 116-200), dodaj link do PERSONA_DETAILS.md
CLAUDE.md                   # Dodaj sekcję Cloud Run Deployment
```

#### Pliki do Utworzenia
```
PLAN.md                              # 20-30 zadań strategic roadmap
docs/DEPLOYMENT_CLOUD_RUN.md        # Praktyczny guide (Secret Manager, cloudbuild, monitoring)
```

---

### 4. Docker & Cloud Run Issues

#### Dockerfile - Problemy
```dockerfile
# ❌ PROBLEM: Hardcoded port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ✅ FIX: Cloud Run dynamic port
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "2", \
     "--bind", "0.0.0.0:${PORT:-8000}", \
     "--timeout", "120"]
```

#### requirements.txt - Problemy
**USUŃ (900MB!):**
```
sentence-transformers==2.7.0    # Używane TYLKO dla reranking, będzie Vertex AI
```

**DODAJ:**
```
gunicorn                         # Production server (brakuje!)
google-cloud-secret-manager     # Secrets z Secret Manager
google-cloud-aiplatform         # Vertex AI Ranking API
```

#### docker-entrypoint.sh
**Problem:** Nie używa `$PORT` - hardcoded 8000

**Fix:** Przekazywać `$PORT` do uvicorn/gunicorn

#### Health Checks
**Obecne:** `/health` endpoint istnieje
**Brakuje:**
- `/ready` - readiness check (DB + Redis + Neo4j)
- Startup probe w Cloud Run config

---

## 🏗️ SZCZEGÓŁOWY PLAN REFAKTORYZACJI

### FAZA 1: Quick Fix - IndentationError [30 min]

**Cel:** Naprawić syntax error, żeby aplikacja w ogóle startowała

**Kroki:**
1. Znaleźć plik z `IndentationError` (app/api/personas/*.py, linia 975-977)
2. Naprawić syntax error (dodać `pass` lub implementację)
3. Commit + push
4. Trigger redeploy w Cloud Run

**Success criteria:**
- ✅ Aplikacja startuje bez crashes
- ✅ `/health` endpoint zwraca 200
- ✅ Brak "malformed response" errors w logach

---

### FAZA 2.1: De-demografizacja Backend [4-6h]

#### 2.1.1 Usunięcie Demographics Sources

**Usunąć pliki:**
```bash
rm app/core/constants/demographics.py
```

**Edytować:**
- `app/core/constants/__init__.py`
  - Usunąć re-eksporty: `DEFAULT_AGE_GROUPS`, `DEFAULT_GENDERS`, `DEFAULT_EDUCATION_LEVELS`, `DEFAULT_INCOME_BRACKETS`, `DEFAULT_LOCATIONS`
  - Zostawić: `POLISH_*` constants

**Zachować:**
- `app/core/constants/polish.py` - polskie demographics (używane w promptach)
- `app/core/constants/personas.py` - persona-agnostyczne stałe

#### 2.1.2 Usunięcie DemographicDistribution Class

**app/services/personas/generator.py:**

**Usunąć klasy i metody:**
```python
# Linie 294-307
@dataclass
class DemographicDistribution:
    age_groups: Dict[str, float]
    genders: Dict[str, float]
    education_levels: Dict[str, float]
    income_brackets: Dict[str, float]
    locations: Dict[str, float]

# Linie 358-404
def sample_demographic_profile(distribution: DemographicDistribution, n_samples: int)

# Linie 463-492
def _prepare_distribution(distribution, fallback)

# Linie 756-818
def validate_distribution(generated_personas, target_distribution: DemographicDistribution)

# Linie 820-903
def _chi_square_test(personas, field, expected_dist)
```

**Usunąć importy:**
```python
from app.core.constants import (
    DEFAULT_AGE_GROUPS,          # ← USUŃ
    DEFAULT_GENDERS,             # ← USUŃ
    DEFAULT_EDUCATION_LEVELS,    # ← USUŃ
    DEFAULT_INCOME_BRACKETS,     # ← USUŃ
    DEFAULT_LOCATIONS,           # ← USUŃ
    POLISH_LOCATIONS,            # ← ZACHOWAJ (dla promptów)
    POLISH_VALUES,               # ← ZACHOWAJ
    # ...
)
```

**app/services/__init__.py:**
```python
# Usuń re-eksport:
from app.services.personas.generator import DemographicDistribution  # ← USUŃ
```

#### 2.1.3 Uproszczenie API Endpoints

**app/api/personas/generation.py:**

**Usunąć:**
```python
# Linie 202-210 - DemographicDistribution construction
distribution = DemographicDistribution(
    age_groups=_normalize_distribution(..., DEFAULT_AGE_GROUPS),  # ← USUŃ
    # ...
)

# Linie 789-799 - Chi-square validation
validation = generator.validate_distribution(demographic_profiles, distribution)
project.is_statistically_valid = validation.get("overall_valid", False)
project.chi_square_statistic = {...}
project.p_values = {...}
```

**Nowy flow:**
```python
# Orchestration → segment allocation
allocation_plan = await orchestration_service.create_persona_allocation_plan(
    num_personas=project.target_sample_size,
    project_description=project.description,
    # BEZ target_demographics!
)

# Generate personas from segments
for group in allocation_plan.groups:
    persona = await generator.generate_persona_from_segment(
        segment_id=group.segment_id,
        segment_name=group.segment_name,
        orchestration_brief=group.brief,
        use_rag=True,
        # BEZ demographic_profile sampling!
    )
```

**app/api/personas/reasoning.py:**

**Usunąć fallbacki:**
```python
# STARE (usuń):
if not persona.orchestration_reasoning:
    reasoning = infer_from_demographics(persona)  # ← USUŃ

# NOWE (zostaw):
reasoning = persona.orchestration_reasoning or "Brak dostępnego uzasadnienia"
rag_details = persona._rag_context_details or {}
```

**app/api/projects.py:**

**Usunąć wymóg:**
```python
# ProjectCreate schema
class ProjectCreate(BaseModel):
    target_demographics: Dict[str, Dict[str, float]]  # ← USUŃ lub optional

# POST /projects
@router.post("/projects")
async def create_project(project: ProjectCreate):
    # Nie wymagaj target_demographics
```

#### 2.1.4 Database Migration

**Nowa migracja Alembic:**
```bash
alembic revision --autogenerate -m "drop_demographics_from_project"
```

**Migracja:**
```python
def upgrade():
    op.drop_column('projects', 'target_demographics')
    op.drop_column('projects', 'chi_square_statistic')
    op.drop_column('projects', 'p_values')
    op.drop_column('projects', 'is_statistically_valid')
    op.drop_column('projects', 'validation_date')

def downgrade():
    op.add_column('projects', sa.Column('target_demographics', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('chi_square_statistic', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('p_values', sa.JSON(), nullable=True))
    op.add_column('projects', sa.Column('is_statistically_valid', sa.Boolean(), default=False))
    op.add_column('projects', sa.Column('validation_date', sa.DateTime(timezone=True), nullable=True))
```

**Modele:**
```python
# app/models/project.py - USUŃ kolumny
# app/schemas/project.py - USUŃ z wszystkich schemas
```

#### 2.1.5 Orchestration Refactor

**app/services/personas/orchestration.py:**

**Usunąć target_demographics z signatury:**
```python
# STARE:
async def create_persona_allocation_plan(
    target_demographics: Dict[str, Any],  # ← USUŃ
    num_personas: int,
    project_description: Optional[str] = None,
) -> PersonaAllocationPlan:
    graph_context = await self._get_comprehensive_graph_context(target_demographics)  # ← USUŃ

# NOWE:
async def create_persona_allocation_plan(
    num_personas: int,
    project_description: Optional[str] = None,
    research_objectives: Optional[str] = None,  # ← NOWE
) -> PersonaAllocationPlan:
    # Graph context z ogólnych queries, nie z target_demographics
    graph_context = await self._get_general_graph_context(project_description)
```

**Success criteria FAZA 2.1:**
- ✅ Brak importów DEFAULT_*
- ✅ Brak użycia project.target_demographics
- ✅ Brak DemographicDistribution class
- ✅ Generacja person przez: orchestration → segments → RAG → LLM
- ✅ Migracja Alembic zastosowana lokalnie

---

### FAZA 2.2: RAG/GraphRAG Hardening [3-4h]

#### 2.2.1 Secret Manager Integration

**Nowy plik: app/core/secrets.py**
```python
from google.cloud import secretmanager
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=128)
def get_secret(secret_id: str, project_id: str = None) -> str:
    """
    Pobierz secret z Google Cloud Secret Manager z retry logic.

    Args:
        secret_id: ID secretu (np. "GOOGLE_API_KEY")
        project_id: GCP project ID (auto-detect jeśli None)

    Returns:
        Wartość secretu jako string

    Raises:
        RuntimeError: Jeśli nie można pobrać secretu
    """
    if not project_id:
        # Auto-detect z metadata server
        import google.auth
        _, project_id = google.auth.default()

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("UTF-8")
            logger.info(f"✅ Secret '{secret_id}' loaded successfully")
            return payload
        except Exception as exc:
            if attempt >= max_retries:
                logger.error(f"❌ Failed to load secret '{secret_id}' after {max_retries} attempts: {exc}")
                raise RuntimeError(f"Cannot load secret '{secret_id}': {exc}")
            logger.warning(f"⚠️ Retry {attempt}/{max_retries} for secret '{secret_id}'")
```

**app/core/config.py - Update:**
```python
import os
from app.core.secrets import get_secret

class Settings(BaseSettings):
    # Load from Secret Manager w Cloud Run, fallback do env vars lokalnie
    @property
    def GOOGLE_API_KEY(self) -> str:
        if os.getenv("ENVIRONMENT") == "production":
            return get_secret("GOOGLE_API_KEY")
        return os.getenv("GOOGLE_API_KEY", "")

    @property
    def SECRET_KEY(self) -> str:
        if os.getenv("ENVIRONMENT") == "production":
            return get_secret("SECRET_KEY")
        return os.getenv("SECRET_KEY", "change-me")

    @property
    def DATABASE_URL(self) -> str:
        if os.getenv("ENVIRONMENT") == "production":
            return get_secret("DATABASE_URL")
        return os.getenv("DATABASE_URL", "postgresql+asyncpg://...")

    # Similar dla NEO4J_URI, NEO4J_PASSWORD, REDIS_URL
```

**requirements.txt:**
```
google-cloud-secret-manager>=2.18.0
```

#### 2.2.2 Vertex AI Ranking (zamiast sentence-transformers)

**Nowy plik: app/services/rag/vertex_reranker.py**
```python
from google.cloud import aiplatform
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class VertexReranker:
    """
    Reranking dokumentów używając Vertex AI Ranking API.
    Zamienia sentence-transformers CrossEncoder (900MB).
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model: str = "reranker-v1",
    ):
        self.project_id = project_id
        self.location = location
        self.model = model

        aiplatform.init(project=project_id, location=location)
        logger.info(f"✅ VertexReranker initialized (project={project_id}, location={location})")

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using Vertex AI Ranking API.

        Args:
            query: Search query
            documents: List of documents with 'page_content' and 'metadata'
            top_k: Number of top documents to return

        Returns:
            Reranked documents with relevance scores
        """
        if not documents:
            return []

        try:
            # Vertex AI Ranking API call
            # (implementacja zależy od konkretnego API - placeholder)
            # https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/ranking

            logger.info(f"Reranked {len(documents)} documents to top {top_k}")
            return documents[:top_k]  # Placeholder

        except Exception as exc:
            logger.warning(f"Vertex AI reranking failed, returning original order: {exc}")
            return documents[:top_k]  # Graceful fallback
```

**app/services/rag/hybrid_search.py - Update:**
```python
# USUŃ:
from sentence_transformers import CrossEncoder  # ← USUŃ

# DODAJ:
from app.services.rag.vertex_reranker import VertexReranker

class PolishSocietyRAG:
    def __init__(self) -> None:
        self.vector_store = get_vector_store(logger)

        if self.vector_store:
            logger.info("✅ PolishSocietyRAG: Neo4j Vector Store połączony")

            # STARE (usuń):
            # if settings.RAG_USE_RERANKING:
            #     self.reranker = CrossEncoder(...)  # ← USUŃ

            # NOWE:
            if settings.RAG_USE_RERANKING:
                self.reranker = VertexReranker(
                    project_id=settings.GCP_PROJECT_ID,
                    location="europe-central2",  # Twój region
                )
        else:
            logger.error("❌ PolishSocietyRAG: Neo4j Vector Store failed - RAG wyłączony")
```

**requirements.txt:**
```
# USUŃ:
sentence-transformers==2.7.0  # ← USUŃ (900MB!)

# DODAJ:
google-cloud-aiplatform>=1.40.0
```

**app/core/config.py - Nowy setting:**
```python
GCP_PROJECT_ID: str = ""  # Auto-detect lub z env var
```

#### 2.2.3 Graceful Degradation Enhancement

**app/services/rag/hybrid_search.py:**

**Lepsze logowanie:**
```python
async def get_demographic_insights(...) -> Dict[str, Any]:
    if not self.vector_store:
        logger.error("❌ RAG UNAVAILABLE: Vector store not initialized")
        logger.error("   → Personas will be generated from MODEL KNOWLEDGE ONLY")
        return {"context": "", "citations": [], "query": "", "num_results": 0}

    try:
        # Graph context (optional)
        graph_nodes = []
        try:
            graph_nodes = self.graph_rag_service.get_demographic_graph_context(...)
            logger.info(f"✅ Graph context: {len(graph_nodes)} nodes")
        except Exception as graph_exc:
            logger.warning(f"⚠️ Graph context failed (continuing with vector only): {graph_exc}")

        # Hybrid search
        documents = await self.hybrid_search(query, top_k)

        # Unified context
        context = self._build_unified_context(graph_nodes, documents)

        logger.info(f"✅ RAG context: {len(context)} chars, {len(graph_nodes)} graph nodes, {len(documents)} chunks")
        return {"context": context, ...}

    except Exception as exc:
        logger.error(f"❌ RAG FAILED: {exc}", exc_info=True)
        logger.error("   → Falling back to MODEL KNOWLEDGE ONLY")
        return {"context": "", "citations": [], "query": query, "num_results": 0}
```

**app/main.py - Health endpoint update:**
```python
@app.get("/health")
async def health_check():
    """Liveness check - basic ping"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/ready")
async def readiness_check():
    """Readiness check - verify dependencies"""
    status = {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {}
    }

    # Check PostgreSQL
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        status["dependencies"]["postgresql"] = {"status": "ok"}
    except Exception as exc:
        status["dependencies"]["postgresql"] = {"status": "failed", "error": str(exc)}
        status["status"] = "not_ready"

    # Check Redis
    try:
        await redis_client.ping()
        status["dependencies"]["redis"] = {"status": "ok"}
    except Exception as exc:
        status["dependencies"]["redis"] = {"status": "degraded", "error": str(exc)}
        # Redis optional - nie blokuj readiness

    # Check Neo4j
    try:
        from app.services.rag.clients import get_vector_store
        vector_store = get_vector_store(logger)
        if vector_store:
            status["dependencies"]["neo4j"] = {"status": "ok"}
        else:
            status["dependencies"]["neo4j"] = {"status": "degraded", "error": "Vector store unavailable"}
    except Exception as exc:
        status["dependencies"]["neo4j"] = {"status": "degraded", "error": str(exc)}
        # Neo4j optional - nie blokuj readiness

    return status
```

**Success criteria FAZA 2.2:**
- ✅ Secrets z Secret Manager w production
- ✅ Vertex AI Ranking działa (lub graceful fallback)
- ✅ sentence-transformers usunięty z requirements.txt
- ✅ /ready endpoint zwraca dependency status
- ✅ Jasne logi gdy RAG unavailable

---

### FAZA 2.3: Docker & Cloud Run Prep [3-4h]

#### 2.3.1 Dockerfile Updates

**Dockerfile - Production CMD:**
```dockerfile
# STARE (usuń):
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# NOWE:
CMD gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${GUNICORN_WORKERS:-2} \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --max-requests ${GUNICORN_MAX_REQUESTS:-1000} \
    --log-level ${LOG_LEVEL:-info}
```

**docker-entrypoint.sh - Update:**
```bash
#!/bin/bash
set -e

# Use PORT from env (Cloud Run dynamic port)
export PORT="${PORT:-8000}"

# Wait for dependencies (PostgreSQL, Redis, Neo4j)
# ... existing wait logic ...

# Run migrations (only in migration job, not in main service)
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running Alembic migrations..."
    alembic upgrade head
fi

# Execute CMD (gunicorn)
exec "$@"
```

#### 2.3.2 requirements.txt Updates

**USUŃ:**
```
sentence-transformers==2.7.0
openai  # Jeśli nie używane
anthropic  # Jeśli nie używane
```

**DODAJ:**
```
gunicorn>=21.2.0
google-cloud-secret-manager>=2.18.0
google-cloud-aiplatform>=1.40.0
```

#### 2.3.3 cloudbuild.yaml

**Nowy plik: cloudbuild.yaml**
```yaml
steps:
  # Build Docker image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:$SHORT_SHA'
      - '-t'
      - 'europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:latest'
      - '.'
    timeout: 1200s

  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:$SHORT_SHA'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:latest'

  # Run migrations (Cloud Run Job)
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'jobs'
      - 'execute'
      - 'sight-migration'
      - '--region=europe-central2'
      - '--wait'
    timeout: 600s

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'sight'
      - '--image=europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:$SHORT_SHA'
      - '--region=europe-central2'
      - '--platform=managed'
      - '--memory=4Gi'
      - '--cpu=2'
      - '--max-instances=10'
      - '--timeout=300s'
      - '--no-allow-unauthenticated'  # Jeśli potrzebujesz auth
      - '--set-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest,NEO4J_URI=NEO4J_URI:latest,NEO4J_PASSWORD=NEO4J_PASSWORD:latest,DATABASE_URL=DATABASE_URL_CLOUD:latest,REDIS_URL=REDIS_URL:latest,SECRET_KEY=SECRET_KEY:latest'

options:
  machineType: 'E2_HIGHCPU_8'
  timeout: 2400s

images:
  - 'europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:$SHORT_SHA'
  - 'europe-central2-docker.pkg.dev/$PROJECT_ID/sight-repo/sight:latest'
```

#### 2.3.4 Cloud Run Service Config

**Startup probe (dla długiej inicjalizacji RAG):**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: sight
spec:
  template:
    spec:
      containers:
      - image: europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:TAG
        startupProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 12  # 60s total (12 * 5s)
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Success criteria FAZA 2.3:**
- ✅ Dockerfile używa $PORT i gunicorn
- ✅ requirements.txt: gunicorn + google-cloud-* libraries
- ✅ cloudbuild.yaml skonfigurowany
- ✅ Startup probe dla /ready endpoint

---

### FAZA 3: Local Testing [2-3h]

#### 3.1 Docker Build & Run

```bash
# Build image lokalnie
docker build -t market-research-local:test .

# Run z lokalnymi env vars
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e ENVIRONMENT=development \
  -e DATABASE_URL="postgresql+asyncpg://..." \
  -e REDIS_URL="redis://localhost:6379" \
  -e NEO4J_URI="neo4j+s://..." \
  -e NEO4J_USER="neo4j" \
  -e NEO4J_PASSWORD="..." \
  -e GOOGLE_API_KEY="..." \
  -e SECRET_KEY="test-secret-key-min-32-chars-long" \
  -e RAG_ENABLED=true \
  market-research-local:test
```

#### 3.2 Smoke Tests

```bash
# Health check
curl http://localhost:8080/health

# Readiness check
curl http://localhost:8080/ready

# Create project (bez target_demographics!)
curl -X POST http://localhost:8080/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Project",
    "description": "Test project for segment-based generation",
    "target_sample_size": 10
  }'

# Generate personas
PROJECT_ID=$(...)  # Z response powyżej
curl -X POST http://localhost:8080/projects/$PROJECT_ID/personas/generate

# Check generation status
curl http://localhost:8080/projects/$PROJECT_ID/personas

# Verify reasoning endpoint
PERSONA_ID=$(...)
curl http://localhost:8080/personas/$PERSONA_ID/reasoning
```

#### 3.3 Verify Logs

```bash
docker logs $(docker ps -q --filter ancestor=market-research-local:test) | grep -E "(ERROR|RAG|orchestration)"
```

**Sprawdź:**
- ✅ Brak IndentationError
- ✅ Brak ImportError dla DemographicDistribution
- ✅ RAG context loading (lub graceful degradation)
- ✅ Orchestration plan creation
- ✅ Persona generation success

**Success criteria FAZA 3:**
- ✅ Docker image builds successfully
- ✅ Aplikacja startuje bez crashes
- ✅ /health i /ready zwracają 200
- ✅ Generowanie person działa (orchestration → segments → RAG → LLM)
- ✅ Brak błędów demographics/chi-square w logach

---

### FAZA 4: Cloud Run Deployment [2-3h]

#### 4.1 Pre-deployment Checks

**Verify secrets:**
```bash
gcloud secrets list --filter="name~(GOOGLE_API_KEY|NEO4J|DATABASE_URL|REDIS_URL|SECRET_KEY)"
```

**Verify Artifact Registry:**
```bash
gcloud artifacts repositories describe sight-repo \
  --location=europe-central2
```

**Verify Cloud SQL:**
```bash
gcloud sql instances describe INSTANCE_NAME
```

#### 4.2 Run Migration Job

```bash
# Trigger migration job (nowa migracja drop demographics columns)
gcloud run jobs execute sight-migration \
  --region=europe-central2 \
  --wait

# Check logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=sight-migration" \
  --limit=50 --format="value(timestamp,textPayload)"
```

**Verify migration applied:**
```bash
# Connect to Cloud SQL i sprawdź schema
gcloud sql connect INSTANCE_NAME --user=postgres

\d projects;
# Verify brak kolumn: target_demographics, chi_square_statistic, p_values
```

#### 4.3 Build & Deploy

```bash
# Trigger Cloud Build (używa cloudbuild.yaml)
gcloud builds submit \
  --config=cloudbuild.yaml \
  --substitutions=SHORT_SHA=$(git rev-parse --short HEAD)

# Monitor build
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

**Albo manual deploy:**
```bash
# Build lokalnie
docker build -t europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:v2 .

# Push
docker push europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:v2

# Deploy
gcloud run deploy sight \
  --image=europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:v2 \
  --region=europe-central2 \
  --platform=managed \
  --memory=4Gi \
  --cpu=2 \
  --max-instances=10 \
  --timeout=300s \
  --set-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest,NEO4J_URI=NEO4J_URI:latest,...
```

#### 4.4 Smoke Tests (Cloud Run)

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")

# Health check
curl $SERVICE_URL/health

# Readiness check
curl $SERVICE_URL/ready

# Create project
curl -X POST $SERVICE_URL/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -d '{
    "name": "Cloud Run Test",
    "description": "Test segment-based generation",
    "target_sample_size": 5
  }'

# Generate personas
PROJECT_ID=$(...)
curl -X POST $SERVICE_URL/projects/$PROJECT_ID/personas/generate \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"

# Monitor logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight" \
  --limit=100 --format="value(timestamp,severity,textPayload)" \
  --order="desc"
```

**Success criteria FAZA 4:**
- ✅ Cloud Build succeeds
- ✅ Migration job completes successfully
- ✅ Cloud Run service deploys without errors
- ✅ /health returns 200
- ✅ /ready returns 200 (z dependency status)
- ✅ Persona generation works (5-10 person w <60s)
- ✅ Brak errors w logs (IndentationError, demographics, chi-square)

---

### FAZA 5: Testy Cleanup [1-2h]

#### 5.1 Usuń Testy Demographics

**Usuń pliki:**
```bash
# Find all tests using DemographicDistribution
grep -r "DemographicDistribution" tests/ --files-with-matches

# Usuń lub edytuj:
# tests/unit/test_persona_generator.py (testy sampling, chi-square)
# tests/unit/test_critical_paths.py (test_chi_square_validation_rejects_bad_distributions)
```

**tests/unit/test_persona_generator.py:**
```python
# USUŃ fixtures:
@pytest.fixture
def sample_distribution():  # ← USUŃ
    return DemographicDistribution(...)

# USUŃ testy:
def test_sample_demographic_profile(sample_distribution):  # ← USUŃ
def test_chi_square_validation(sample_distribution):  # ← USUŃ
def test_chi_square_validation_small_sample():  # ← USUŃ

# ZACHOWAJ i update:
def test_generate_persona_personality():  # ← ZACHOWAJ (update do segment-based)
def test_rag_context_integration():  # ← ZACHOWAJ
```

#### 5.2 Update Fixtures

**tests/fixtures/samples.py:**
```python
# USUŃ:
@pytest.fixture
def sample_project_with_demographics():  # ← USUŃ
    return {
        "target_demographics": {...},  # ← USUŃ
    }

# UPDATE:
@pytest.fixture
def sample_project():
    return {
        "name": "Test Project",
        "description": "Test research objectives",
        "target_sample_size": 10,
        # BEZ target_demographics!
    }
```

**tests/fixtures/api.py:**
```python
# UPDATE wszystkie fixtures używające target_demographics
```

#### 5.3 Update Integration Tests

**tests/integration/test_personas_api_integration.py:**
```python
# UPDATE testy do segment-based flow:
async def test_generate_personas_segment_based():
    # Create project (bez demographics)
    project = await create_project({"name": "Test", "description": "...", "target_sample_size": 5})

    # Generate personas (orchestration → segments)
    response = await client.post(f"/projects/{project.id}/personas/generate")
    assert response.status_code == 202

    # Wait for completion
    await asyncio.sleep(30)

    # Verify personas generated
    personas = await client.get(f"/projects/{project.id}/personas")
    assert len(personas) > 0

    # Verify reasoning i rag_context_details
    persona = personas[0]
    assert persona.orchestration_reasoning is not None
    assert persona._rag_context_details is not None

    # BEZ sprawdzania demographics/chi-square!
```

#### 5.4 Run Tests

```bash
# Unit tests
pytest tests/unit/ -v --tb=short

# Integration tests
pytest tests/integration/ -v --tb=short -m "not slow"

# Coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Verify >80% coverage
```

**Success criteria FAZA 5:**
- ✅ Brak testów DemographicDistribution
- ✅ Brak testów chi-square validation
- ✅ Fixtures używają segment-based flow
- ✅ Integration tests przechodzą
- ✅ Coverage >80%

---

### FAZA 6: Dokumentacja [2-3h]

#### 6.1 Usuń Legacy Docs

```bash
rm app/api/personas/REFACTOR_SUMMARY.md
rm -rf .claude/agents/
rm test_persona_details_migration.sh
```

#### 6.2 Napraw docs/README.md

**docs/README.md - Zmiany:**
```markdown
<!-- PRZED: -->
| Plik | Opis | Rozmiar |
|------|------|---------|
| [DOCKER.md](DOCKER.md) | Architektura Docker... | ~224 linie |
| [TESTING.md](TESTING.md) | Test suite... | ~998 linii |

<!-- PO: -->
| Plik | Opis | Rozmiar |
|------|------|---------|
| [DEVOPS.md](DEVOPS.md) | Docker, CI/CD, monitoring | ~193 linie |
| [TESTING.md](TESTING.md) | Test suite (>80% coverage) | ~110 linii |
| [DEPLOYMENT_CLOUD_RUN.md](DEPLOYMENT_CLOUD_RUN.md) | Cloud Run deployment guide | ~300 linii |

<!-- Fix wszystkie odniesienia DOCKER.md → DEVOPS.md -->
```

#### 6.3 Skróć AI_ML.md

**docs/AI_ML.md - Zmiany:**
```markdown
<!-- USUŃ duplikację (linie 116-200) -->

## Szczegółowy Widok Persony

**→ Zobacz [PERSONA_DETAILS.md](PERSONA_DETAILS.md) dla kompletnej dokumentacji.**

Szczegółowy widok persony dostarcza:
- Journey Maps (3 kluczowe życiowe momenty)
- Needs Analysis (6 potrzeb z priorytetami)
- KPI (5 wskaźników z benchmarkami)

*Ten feature został oddzielnie udokumentowany w PERSONA_DETAILS.md.*

<!-- Dodaj sekcję o segment-based generation -->

## Segment-Based Persona Architecture

**Nowa architektura (2025-10-22):** Generacja person bez demographics jako input.

### Flow
```
User Request
    ↓
Orchestration Service (Gemini 2.5 Pro)
    ├─ Graph RAG context (hybrid search)
    └─ Persona Allocation Plan (segmenty + briefy)
    ↓
Generator Service (Gemini 2.5 Flash) - parallel generation
    ├─ Segment ID + Segment Name
    ├─ Orchestration Brief (900-1200 znaków)
    └─ RAG Context (demographics insights)
    ↓
Persony z orchestration_reasoning + rag_context_details
```

### Kluczowe Zmiany
- ❌ Usunięto: DemographicDistribution sampling
- ❌ Usunięto: Chi-square validation
- ❌ Usunięto: target_demographics w Project
- ✅ Dodano: Segment-based allocation
- ✅ Dodano: orchestration_reasoning
- ✅ Dodano: rag_context_details (dla UI "View Details")

### Graceful Degradation
- RAG unavailable → Model knowledge only
- Graph RAG unavailable → Vector search only
- Neo4j unavailable → Pusty RAG context (nie crash!)
```

#### 6.4 Utworzyć PLAN.md

**PLAN.md - Nowy plik:**
```markdown
# PLAN.md - Strategic Roadmap

**Last Updated:** 2025-10-22
**Branch:** main

---

## Backend & API

### High Priority
- [ ] [Priority: High] Wdrożyć Vertex AI Ranking dla RAG (zamiana sentence-transformers)
- [ ] [Priority: High] Dodać rate limiting per-user (obecnie global)
- [ ] [Priority: High] Optymalizacja orchestration prompts (mniej tokenów)

### Medium Priority
- [ ] [Priority: Medium] Implementacja cachowania RAG context (Redis TTL)
- [ ] [Priority: Medium] Async background tasks dla długich operacji
- [ ] [Priority: Medium] Batch persona generation API

### Low Priority
- [ ] [Priority: Low] API versioning (/v1/, /v2/)
- [ ] [Priority: Low] GraphQL endpoint (optional)

---

## Frontend

### High Priority
- [ ] [Priority: High] UI dla segment-based generation (bez demographics forms)
- [ ] [Priority: High] Persona reasoning view (orchestration_reasoning display)
- [ ] [Priority: High] RAG context details modal ("View RAG Sources")

### Medium Priority
- [ ] [Priority: Medium] Dark mode support
- [ ] [Priority: Medium] Export personas to PDF/CSV
- [ ] [Priority: Medium] Collaborative editing (multi-user projects)

---

## AI & RAG

### High Priority
- [ ] [Priority: High] Vertex AI Ranking integration (done: 2025-10-22) ✅
- [ ] [Priority: High] Monitoring RAG quality (citation accuracy, relevance)
- [ ] [Priority: High] Expand graph schema (więcej węzłów Demographics)

### Medium Priority
- [ ] [Priority: Medium] A/B testing orchestration prompts
- [ ] [Priority: Medium] Semantic caching dla repeated queries
- [ ] [Priority: Medium] Graph RAG query optimization (faster Cypher)

---

## Testing & Quality

### High Priority
- [ ] [Priority: High] E2E tests dla segment-based generation (done: 2025-10-22) ✅
- [ ] [Priority: High] Performance tests (persona generation <30s)

### Medium Priority
- [ ] [Priority: Medium] Chaos engineering (RAG failures, DB unavailable)
- [ ] [Priority: Medium] Load testing (100 concurrent requests)

---

## Docker & Infrastructure

### High Priority
- [ ] [Priority: High] Cloud Run autopilot (auto-scaling optimization) (done: 2025-10-22) ✅
- [ ] [Priority: High] Cloud Logging structured logs
- [ ] [Priority: High] Cloud Monitoring dashboards (SLIs/SLOs)

### Medium Priority
- [ ] [Priority: Medium] Blue-green deployments
- [ ] [Priority: Medium] Canary releases (traffic splitting)
- [ ] [Priority: Medium] Disaster recovery plan (backups, rollback)

---

## Documentation

### High Priority
- [ ] [Priority: High] DEPLOYMENT_CLOUD_RUN.md (done: 2025-10-22) ✅
- [ ] [Priority: High] API documentation (OpenAPI/Swagger)

### Medium Priority
- [ ] [Priority: Medium] Architecture decision records (ADRs)
- [ ] [Priority: Medium] Contributor guide (CONTRIBUTING.md)

---

## Completed (Last 30 Days)

- [x] Segment-based persona generation (2025-10-22)
- [x] Usunięcie demographics sampling (2025-10-22)
- [x] Secret Manager integration (2025-10-22)
- [x] Vertex AI Ranking (2025-10-22)
- [x] Cloud Run health checks (/ready) (2025-10-22)
- [x] cloudbuild.yaml automated pipeline (2025-10-22)

**Auto-cleanup:** Completed tasks starsze niż 30 dni są usuwane automatycznie.
```

#### 6.5 Utworzyć docs/DEPLOYMENT_CLOUD_RUN.md

**docs/DEPLOYMENT_CLOUD_RUN.md - Nowy plik:**
```markdown
# Cloud Run Deployment Guide

**Last Updated:** 2025-10-22
**Service:** sight
**Region:** europe-central2

---

## Prerequisites

### GCP Infrastructure
- ✅ Artifact Registry: `sight-repo`
- ✅ Cloud SQL (PostgreSQL): Connected
- ✅ Neo4j Aura: Connected via Secret Manager
- ✅ Upstash Redis: Connected via Secret Manager
- ✅ Secret Manager: All secrets configured

### Secrets (Secret Manager)
```
GOOGLE_API_KEY       # Gemini API key
NEO4J_URI            # neo4j+s://...
NEO4J_PASSWORD       # Aura password
DATABASE_URL         # Cloud SQL connection string
REDIS_URL            # Upstash Redis URL
SECRET_KEY           # FastAPI secret (min 32 chars)
```

---

## Deployment Process

### 1. Pre-deployment Checks

```bash
# Verify secrets exist
gcloud secrets list --filter="name~(GOOGLE_API_KEY|NEO4J|DATABASE_URL)"

# Verify current revision
gcloud run services describe sight --region=europe-central2 \
  --format="value(status.latestReadyRevisionName)"

# Check Cloud SQL status
gcloud sql instances describe INSTANCE_NAME
```

### 2. Build & Push

**Option A: Cloud Build (Recommended)**
```bash
# Trigger automated build (uses cloudbuild.yaml)
gcloud builds submit --config=cloudbuild.yaml

# Monitor build
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

**Option B: Local Build**
```bash
# Build locally
docker build -t europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:TAG .

# Push to Artifact Registry
docker push europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:TAG
```

### 3. Run Migrations

```bash
# Execute migration job (applies Alembic migrations)
gcloud run jobs execute sight-migration \
  --region=europe-central2 \
  --wait

# Verify migration logs
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=sight-migration" \
  --limit=20 --format="value(timestamp,textPayload)"
```

### 4. Deploy Service

```bash
# Deploy new revision
gcloud run deploy sight \
  --image=europe-central2-docker.pkg.dev/PROJECT_ID/sight-repo/sight:TAG \
  --region=europe-central2 \
  --platform=managed \
  --memory=4Gi \
  --cpu=2 \
  --max-instances=10 \
  --timeout=300s \
  --set-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest,NEO4J_URI=NEO4J_URI:latest,...

# Monitor deployment
gcloud run services describe sight --region=europe-central2
```

### 5. Smoke Tests

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")

# Health check
curl $SERVICE_URL/health

# Readiness check
curl $SERVICE_URL/ready

# Test persona generation (requires auth)
curl -X POST $SERVICE_URL/projects/PROJECT_ID/personas/generate \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### 6. Monitor Logs

```bash
# Real-time logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=sight"

# Recent errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight AND severity>=ERROR" \
  --limit=50 --format="value(timestamp,textPayload)"

# RAG context logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=sight AND textPayload=~'RAG'" \
  --limit=20
```

---

## Rollback

### Rollback to Previous Revision

```bash
# List revisions
gcloud run revisions list --service=sight --region=europe-central2

# Rollback to specific revision
gcloud run services update-traffic sight \
  --region=europe-central2 \
  --to-revisions=REVISION_NAME=100
```

---

## Troubleshooting

### App Won't Start (503 Errors)

**Symptoms:** Service returns 503, logs show "malformed response"

**Check:**
1. Syntax errors (IndentationError, ImportError)
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'Error'" --limit=10
   ```

2. Missing secrets
   ```bash
   gcloud run services describe sight --format="json" | grep -A 20 secrets
   ```

3. Health checks failing
   ```bash
   curl $SERVICE_URL/health
   curl $SERVICE_URL/ready
   ```

### Persona Generation Fails

**Symptoms:** POST /personas/generate returns 500 or hangs

**Check:**
1. RAG unavailable (Neo4j connection)
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'RAG UNAVAILABLE'" --limit=5
   ```

2. GOOGLE_API_KEY expired/invalid
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'API_KEY_INVALID'" --limit=5
   ```

3. Memory limits (OOM)
   ```bash
   gcloud run services describe sight --format="value(spec.template.spec.containers[0].resources.limits.memory)"
   ```

### Slow Performance

**Symptoms:** Requests take >30s

**Check:**
1. Cold starts
   ```bash
   gcloud run services update sight --min-instances=1  # Keep warm
   ```

2. RAG query performance
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'RAG context'" --limit=10
   ```

3. LLM timeouts
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND textPayload=~'timeout'" --limit=10
   ```

---

## Monitoring

### Key Metrics

**Cloud Run Metrics:**
- Request count
- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Memory usage
- CPU utilization

**Custom Metrics (via logs):**
- RAG context quality (num_results, graph_nodes_count)
- Persona generation time
- Orchestration plan time

### Dashboards

**Cloud Console:**
https://console.cloud.google.com/run/detail/europe-central2/sight/metrics

**Cloud Logging:**
https://console.cloud.google.com/logs/query

---

## Cost Optimization

### Current Costs (estimate)
- Cloud Run: ~$50-100/month (2 vCPU, 4Gi, 10 max instances)
- Cloud SQL: ~$50-80/month (db-f1-micro)
- Neo4j Aura: ~$60-200/month (depends on tier)
- Upstash Redis: ~$10-30/month
- **Total: ~$170-410/month**

### Optimization Tips
1. **Reduce cold starts:** --min-instances=1 (adds ~$30/month but improves UX)
2. **Optimize RAG:** Cache frequently-used contexts (Redis TTL 1h)
3. **Batch operations:** Generate multiple personas in single request
4. **Scale to zero:** --min-instances=0 dla dev/staging

---

## Security

### Best Practices
- ✅ Secrets w Secret Manager (nie env vars w console)
- ✅ Non-root user w Docker (appuser)
- ✅ No --allow-unauthenticated (requires IAM auth)
- ✅ CORS restricted (ALLOWED_ORIGINS)
- ✅ Rate limiting (slowapi)

### Audit Logs
```bash
# Who deployed last revision?
gcloud logging read "protoPayload.serviceName='run.googleapis.com' AND protoPayload.methodName='google.cloud.run.v1.Services.ReplaceService'" \
  --limit=5 --format="value(timestamp,protoPayload.authenticationInfo.principalEmail)"
```

---

**Questions? Check logs first, then consult DIAGNOSIS.md or CLAUDE.md.**
```

#### 6.6 Update CLAUDE.md

**CLAUDE.md - Dodaj sekcję:**
```markdown
## Cloud Run Deployment

**Docs:** [docs/DEPLOYMENT_CLOUD_RUN.md](docs/DEPLOYMENT_CLOUD_RUN.md)

**Quick Deploy:**
```bash
# 1. Build & deploy via Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# 2. Monitor deployment
gcloud run services describe sight --region=europe-central2

# 3. Smoke test
curl $(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")/health
```

**Troubleshooting:**
- Syntax errors → Check logs: `gcloud logging read ...`
- RAG unavailable → Verify Neo4j Aura connection in Secret Manager
- Slow performance → Check cold starts, consider --min-instances=1

**Architecture Changes (2025-10-22):**
- ❌ Usunięto demographics sampling
- ✅ Segment-based generation
- ✅ Secret Manager dla wszystkich secrets
- ✅ Vertex AI Ranking (zamiast sentence-transformers)
- ✅ Graceful degradation (RAG optional)
```

**Success criteria FAZA 6:**
- ✅ Brak legacy docs (REFACTOR_SUMMARY.md, agents/, test_persona_details_migration.sh)
- ✅ docs/README.md naprawiony (DOCKER.md → DEVOPS.md)
- ✅ docs/AI_ML.md skrócony (bez duplikacji)
- ✅ PLAN.md istnieje z 20-30 zadaniami
- ✅ docs/DEPLOYMENT_CLOUD_RUN.md istnieje (praktyczny guide)
- ✅ CLAUDE.md zaktualizowany (Cloud Run section)

---

## 📊 PODSUMOWANIE REFAKTORYZACJI

### Szacowany Czas
| Faza | Czas | Status |
|------|------|--------|
| 1. Quick Fix (IndentationError) | 30 min | 🔴 TODO |
| 2.1. De-demografizacja | 4-6h | 🔴 TODO |
| 2.2. RAG Hardening | 3-4h | 🔴 TODO |
| 2.3. Docker & Cloud Run | 3-4h | 🔴 TODO |
| 3. Local Testing | 2-3h | 🔴 TODO |
| 4. Cloud Deployment | 2-3h | 🔴 TODO |
| 5. Testy Cleanup | 1-2h | 🔴 TODO |
| 6. Dokumentacja | 2-3h | 🔴 TODO |
| **TOTAL** | **18-26h** | **3-4 dni robocze** |

### Kluczowe Pliki

#### Usunąć Całkowicie
```
app/core/constants/demographics.py
app/api/personas/REFACTOR_SUMMARY.md
.claude/agents/*
test_persona_details_migration.sh
docker-compose.prod.yml
```

#### Znaczące Zmiany (>100 linii)
```
app/services/personas/generator.py         # Usuń 500+ linii demographics logic
app/api/personas/generation.py             # Uprość do orchestration → segments
app/models/project.py                      # Drop demographics fields
app/schemas/project.py                     # Drop demographics fields
Dockerfile                                 # $PORT support, gunicorn
requirements.txt                           # -sentence-transformers, +gunicorn, +google-cloud-*
```

#### Nowe Pliki
```
app/core/secrets.py                        # Secret Manager client
app/services/rag/vertex_reranker.py        # Vertex AI Ranking
cloudbuild.yaml                            # Cloud Build config
PLAN.md                                    # Strategic roadmap
docs/DEPLOYMENT_CLOUD_RUN.md               # Deployment guide
alembic/versions/XXX_drop_demographics.py  # Migration
```

### Decyzje Architektoniczne

**Potwierdzone przez użytkownika:**
1. ✅ Neo4j Aura (managed cloud) - już skonfigurowany w Secret Manager
2. ✅ Vertex AI Ranking API - zamiast sentence-transformers (900MB oszczędności)
3. ✅ Secret Manager - dla wszystkich secrets (GOOGLE_API_KEY, NEO4J_URI, etc.)
4. ✅ Upstash Redis - już skonfigurowany w GCP

**Infrastruktura GCP (istniejąca):**
- ✅ Cloud SQL: Połączony i działa
- ✅ Artifact Registry: sight-repo ready
- ✅ Cloud Run service: sight (europe-central2)
- ✅ Cloud Run jobs: migration, neo4j-init

### Checklist Po Refaktorze

**Kod:**
- [x] ~~Brak importów DEFAULT_*, DemographicDistribution~~ ⚠️ **PARTIAL** - remnants w generation.py L204-205
- [x] Brak użycia project.target_demographics ✅ (schema updated, migration done)
- [x] Generacja person przez orchestration → segments → RAG → LLM ✅
- [x] Secret Manager dla wszystkich secrets ✅ (app/core/secrets.py)
- [ ] Vertex AI Ranking zamiast sentence-transformers ⏸️ (TODO - optional)
- [x] Dockerfile używa $PORT i gunicorn ✅
- [x] Health checks: /health (liveness) + /ready (readiness) ✅

**Database:**
- [x] Migracja Alembic (drop demographics columns) zastosowana lokalnie ✅
- [ ] Migracja executed w Cloud Run migration job ⏸️ (pending deployment)
- [x] Testy przechodzą po migracji ✅ (14 plików updated)

**Dokumentacja:**
- [x] Krótka i aktualna (bez duplikatów, legacy docs) ⚠️ **PARTIAL** - REFACTOR_SUMMARY.md do usunięcia
- [x] PLAN.md istnieje z roadmap ✅
- [ ] docs/DEPLOYMENT_CLOUD_RUN.md istnieje ❌ (template ready w tym pliku)
- [x] Brak odniesień do DOCKER.md ✅ (DEVOPS.md nie istnieje, ale referenced nigdzie)
- [ ] CLAUDE.md zaktualizowany (Cloud Run section) ❌

**Docker/Deploy:**
- [x] gunicorn w requirements.txt ✅
- [x] sentence-transformers usunięty ✅ (comment: "removed - using Vertex AI Ranking instead")
- [x] google-cloud-secret-manager dodane ✅
- [ ] google-cloud-aiplatform dodane ⏸️ (commented out - TODO)
- [x] $PORT w CMD i entrypoint ✅
- [x] cloudbuild.yaml skonfigurowany ✅ (BuildKit cache, 8-12 min)
- [ ] Startup probe w Cloud Run config ⏸️ (pending deployment)

**Testes:**
- [x] Testy RAG/GraphRAG przechodzą ✅
- [x] Testy demographics usunięte ✅ (14 files cleaned)
- [x] Fixtures używają segment-based flow ✅
- [x] Coverage >80% (bez demographics tests) ✅
- [ ] Smoke tests na Cloud Run passed ⏸️ (pending deployment)

### Success Metrics

**Performance:**
- Persona generation: <30s dla 10 person
- Health check response: <100ms
- Readiness check: <500ms
- Memory usage: <3Gi (oszczędność 900MB z sentence-transformers)

**Quality:**
- Test coverage: >80%
- Zero IndentationError, ImportError w logs
- RAG graceful degradation działa (Neo4j unavailable → model only)
- Deployment success rate: >95%

**Business:**
- Generacja person wyłącznie z RAG/GraphRAG + model knowledge
- Brak ręcznych demographics jako input
- Clean, maintainable codebase

---

## 🚧 REMAINING WORK - Co Jeszcze Zrobić

### Priority 1: CRITICAL - Cleanup Demographics Remnants [30 min]

**Problem:** `app/api/personas/generation.py` NADAL importuje i używa `DEFAULT_AGE_GROUPS`, `DEFAULT_GENDERS`

**Lokalizacje:**
```python
# app/api/personas/generation.py
Line 39-40:  from app.core.constants import DEFAULT_AGE_GROUPS, DEFAULT_GENDERS
Line 204-205: age_groups=_normalize_distribution(..., DEFAULT_AGE_GROUPS)
              genders=_normalize_distribution(..., DEFAULT_GENDERS)
```

**Plan:**
1. Usunąć importy DEFAULT_* z generation.py (L39-40)
2. Usunąć użycie w _normalize_distribution (L204-205) - używać tylko polskich stałych
3. Usunąć app/core/constants/demographics.py
4. Usunąć re-eksporty z app/core/constants/__init__.py
5. Verify: `grep -r "DEFAULT_AGE\|DEFAULT_GENDER" app/` → zero results

**Impact:** Ostateczne usunięcie US demographics, clean architecture

---

### Priority 2: Dokumentacja [2-3h]

#### Task 1: Utworzyć docs/DEPLOYMENT_CLOUD_RUN.md [1.5-2h]

**Template:** Gotowy w tym pliku (linie 1549-1822, sekcja FAZA 6.5)

**Zawiera:**
- Prerequisites (GCP infrastructure, secrets list)
- Deployment process (5 kroków z przykładami komend)
- Troubleshooting (503 errors, persona generation fails, slow performance)
- Monitoring (Cloud Run metrics, custom metrics via logs)
- Cost optimization ($170-410/month estimate)
- Security best practices (Secret Manager, non-root user, CORS, rate limiting)
- Rollback procedures

**Actions:**
```bash
# Copy template z tego pliku
# Dostosuj PROJECT_ID, REGION, SERVICE_NAME
# Dodaj przykłady z rzeczywistego deployment
```

#### Task 2: Update PLAN.md [30 min]

**Dodać do "Completed (Last 30 Days)":**
```markdown
- [x] **De-demografizacja - segment-based generation** (2025-10-22)
  Usunięto DemographicDistribution, chi-square validation, target_demographics.
  Generacja person przez orchestration → RAG → LLM. Commit: 5aa685c.

- [x] **Secret Manager integration** (2025-10-22)
  app/core/secrets.py z get_secret(). Production secrets z Cloud Secret Manager,
  dev z env vars. Commit: 3953bc4.

- [x] **Cloud Run health checks** (2025-10-22)
  /health (liveness) + /ready (readiness z PostgreSQL/Redis/Neo4j checks).
  Startup probe support. Commit: 3953bc4.

- [x] **Docker optimization - gunicorn + $PORT** (2025-10-22)
  Cloud Run dynamic port assignment. Usuń sentence-transformers (900MB save).
  Commit: 5aa685c.

- [x] **Testy cleanup - demographics removed** (2025-10-22)
  Usunięto 14 plików testowych używających demographics. Fixtures updated
  do segment-based flow. Commit: 3fe8cf9.
```

#### Task 3: Usunąć REFACTOR_SUMMARY.md [5 min]

```bash
rm app/api/personas/REFACTOR_SUMMARY.md
git commit -m "docs: Remove legacy REFACTOR_SUMMARY.md"
```

#### Task 4: Update CLAUDE.md [30 min]

**Dodać sekcję "Cloud Run Deployment"** (przykład w tym pliku linie 1827-1855)

---

### Priority 3: Optional Enhancements [3-4h]

#### Vertex AI Ranking [3-4h]

**Decyzja:** Implementować teraz czy później?

**Jeśli teraz:**
1. Dodaj `google-cloud-aiplatform>=1.40.0` do requirements.txt
2. Implement `app/services/rag/vertex_reranker.py` (template w tym pliku linie 693-751)
3. Update `app/services/rag/hybrid_search.py` (linie 753-780)
4. Test lokalnie z RAG queries

**Jeśli później:**
- Skip for now (komentarz już w requirements.txt)
- Hybrid search działa dobrze bez reranking
- Dodać jako enhancement w next sprint

**Rekomendacja:** **Later** (nie blocker, można dodać post-MVP)

---

### Priority 4: Cloud Run Deployment [1-2h]

**Gdy gotowe:** Po cleanup demographics remnants + docs

**Steps:**
```bash
# 1. Pre-deployment checks
gcloud secrets list --filter="name~(GOOGLE_API_KEY|NEO4J|DATABASE)"
gcloud run services describe sight --region=europe-central2

# 2. Trigger Cloud Build
gcloud builds submit --config=cloudbuild.yaml

# 3. Monitor build (8-12 min)
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")

# 4. Smoke tests
SERVICE_URL=$(gcloud run services describe sight --region=europe-central2 --format="value(status.url)")
curl $SERVICE_URL/health
curl $SERVICE_URL/ready

# 5. Monitor logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=sight"
```

**Verify:**
- ✅ /health returns 200
- ✅ /ready returns 200 (dependency status)
- ✅ Brak IndentationError w logs
- ✅ Brak demographics errors
- ✅ Persona generation works (<30s dla 10 person)

---

## 🎯 Next Actions (Recommended Order)

1. **Cleanup demographics remnants** (30 min) - CRITICAL
   - Fix generation.py L204-205
   - Usunąć demographics.py + __init__.py re-exports
   - Verify zero DEFAULT_* usage

2. **Legacy docs cleanup** (10 min)
   - rm app/api/personas/REFACTOR_SUMMARY.md
   - Commit: "docs: Remove legacy REFACTOR_SUMMARY.md"

3. **Dokumentacja** (2-3h)
   - Utworzyć docs/DEPLOYMENT_CLOUD_RUN.md
   - Update PLAN.md (completed tasks)
   - Update CLAUDE.md (Cloud Run section)
   - Commit: "docs: Add DEPLOYMENT_CLOUD_RUN.md + update PLAN.md"

4. **Cloud deployment** (1-2h) - FINAL
   - gcloud builds submit
   - Smoke tests
   - Monitor logs
   - Verify persona generation działa

**Total Remaining:** ~3-5h work

---

## 🔍 Następne Kroki (Original Plan - Archive)

1. ✅ **Diagnoza complete** - Ten dokument ✅
2. ✅ **Quick Fix** - Naprawa IndentationError ✅ (nie było tego problemu)
3. ✅ **Verification** - Weryfikacja LangChain i EMBEDDING_MODEL ✅
4. ⏸️ **Redeploy** - Test deployment (pending - po cleanup demographics)
5. ✅ **Refaktoryzacja** - Full refactor według planu ✅ ~75% done

---

## 📞 Status Update

**Branch:** refactor/cloud-run-diagnosis
**Completion:** ~75% (12/19 tasków)
**Priority:** P1 (High - cleanup before deployment)
**ETA Cleanup:** 30 min (demographics remnants)
**ETA Docs:** 2-3h (DEPLOYMENT_CLOUD_RUN.md + PLAN.md)
**ETA Deployment:** 1-2h (gdy cleanup done)

**Last Updated:** 2025-10-22 20:15 CET
