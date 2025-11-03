# Struktura Serwisów

**Ostatnia aktualizacja:** 2025-10-27
**Reorganizacja:** Serwisy pogrupowane według obszarów funkcjonalnych

---

## 📁 Struktura Folderów

```
app/services/
├── shared/         # Wspólne narzędzia (LLM clients)
├── personas/       # Zarządzanie personami
├── focus_groups/   # Grupy fokusowe i dyskusje
├── rag/            # RAG & Knowledge Graph
├── surveys/        # Ankiety
├── dashboard/      # Dashboard metrics & analytics (NOWY)
└── archived/       # Legacy code
```

---

## 🔧 shared/ - Wspólne Narzędzia

**Pliki:**
- `clients.py` - LLM clients (build_chat_model, get_embeddings)

**Import:**
```python
from app.services.shared import build_chat_model
```

---

## 🎭 personas/ - Zarządzanie Personami

**Serwisy:**
- `PersonaGeneratorLangChain` - Generowanie person z RAG (Gemini Flash)
- `PersonaOrchestrationService` - Alokacja person do segmentów
- `PersonaValidator` - Walidacja person (chi-kwadrat)
- `PersonaDetailsService` - Detail View orchestrator
- `PersonaNeedsService` - JTBD analysis (Gemini Pro)
- `PersonaAuditService` - Audit log
- `SegmentBriefService` - **NOWY** - Segment briefs (Redis cache, 7 dni)

**Import:**
```python
from app.services.personas import PersonaGeneratorLangChain, SegmentBriefService
```

---

## 💬 focus_groups/ - Grupy Fokusowe

**Serwisy:**
- `FocusGroupServiceLangChain` - Orkiestracja dyskusji (async parallel)
- `DiscussionSummarizerService` - AI-powered podsumowania
- `MemoryServiceLangChain` - Event sourcing + semantic search

**Import:**
```python
from app.services.focus_groups import FocusGroupServiceLangChain
```

---

## 🔍 rag/ - RAG & Knowledge Graph

**Serwisy:**
- `RAGDocumentService` - Document management (ingest, CRUD)
- `GraphRAGService` - Graph RAG (Cypher queries, answer_question)
- `PolishSocietyRAG` - Hybrid search (vector + keyword + RRF)
- `get_graph_store`, `get_vector_store` - Neo4j clients

**Import:**
```python
from app.services.rag import PolishSocietyRAG, GraphRAGService
```

---

## 📊 surveys/ - Ankiety

**Serwisy:**
- `SurveyResponseGenerator` - Generowanie odpowiedzi person na ankiety

**Import:**
```python
from app.services.surveys import SurveyResponseGenerator
```

---

## ⚙️ Configuration in Services

**All services now use centralized configuration from `config/`:**

```python
# Import configuration modules
from config import models, prompts, rag, demographics, features

# 1. LLM Models (with fallback chain)
model_config = models.get("personas", "generation")  # domain, subdomain
llm = build_chat_model(**model_config.params)

# 2. Prompts (YAML-based, versioned)
jtbd_prompt = prompts.get("personas.jtbd")
rendered_messages = jtbd_prompt.render(
    age=persona.age,
    occupation=persona.occupation
)

# 3. RAG Settings
chunk_size = rag.chunking.chunk_size  # 1000
use_hybrid = rag.retrieval.use_hybrid_search  # True

# 4. Demographics
locations = demographics.poland.locations  # {city: probability}
age_groups = demographics.common.age_groups  # {range: probability}

# 5. Feature Flags
if features.rag.enabled:
    # Use RAG system
    context = rag_service.get_context(query)

if features.orchestration.enabled:
    # Use orchestration service
    result = orchestration_service.orchestrate(project_id)
```

**Migration from app.core.config:**

```python
# OLD (deprecated, but still works via adapter)
from app.core.config import get_settings
settings = get_settings()
model = settings.PERSONA_GENERATION_MODEL

# NEW (recommended)
from config import models
model_config = models.get("personas", "generation")
model = model_config.model
```

**Benefits:**
- ✅ Single Source of Truth (all config in YAML)
- ✅ Hot Reloadable (update YAML without code changes)
- ✅ Type Safe (full type annotations)
- ✅ Version Controlled (track changes in git)

**See:** `config/README.md` for complete configuration guide.

---

## 🔄 Backward Compatibility

**Wszystkie stare importy działają:**
```python
# STARY (deprecated, ale działa)
from app.services import PersonaGenerator, FocusGroupService

# NOWY (zalecany)
from app.services.personas import PersonaGeneratorLangChain
from app.services.focus_groups import FocusGroupServiceLangChain
```

---

## 📦 Centralizacja Konfiguracji (2025-11-03)

### Prompty → `config/prompts/` (YAML)
- `personas/` - JTBD, segment, brief, uniqueness
- `focus_groups/` - Persona responses, summaries
- `rag/` - Cypher, Graph RAG, graph transformer
- Pełna dokumentacja: `config/README.md`

### Stałe Demograficzne → `config/demographics/` (YAML)
- `poland.yaml` - Polskie dane (imiona, miasta, zawody)
- `international.yaml` - Międzynarodowe dane
- `common.yaml` - Wspólne kategorie (age_groups, education_levels)

**Import (nowy sposób):**
```python
from config import prompts, demographics

# Prompty
jtbd_prompt = prompts.get("personas.jtbd")
rendered_messages = jtbd_prompt.render(age=30, occupation="Engineer")

# Demografia
poland_locations = demographics.poland.locations
age_groups = demographics.common.age_groups
```

---

## 📊 dashboard/ - Dashboard Metrics & Analytics

**NOWY (2025-10-27)** - Figma Make Implementation + Optimizations

**Serwisy:**
- `DashboardOrchestrator` - **NEW** - Orchestrates all dashboard services, Redis caching (30-60s)
- `DashboardMetricsService` - KPI calculations (TTI, adoption rate, coverage)
- `ProjectHealthService` - Health assessment & blocker detection
- `QuickActionsService` - Next Best Action recommendations
- `InsightTraceabilityService` - Insight details & evidence trail
- `UsageTrackingService` - Token usage & cost tracking
- `NotificationService` - User notifications & alerts

**Features (Phase 1 + 2):**
- **Insight Types Distribution** - opportunity/risk/trend/pattern aggregation
- **Redis Caching** - 30s TTL for analytics, 60s for usage (hit ratio ~90%)
- **N+1 Optimization** - GROUP BY subqueries (87% fewer queries)
- **Filter Parameters** - project_id, top_n filters for analytics
- **Budget Limit** - Plan-based: free=$50, pro=$100, enterprise=$500
- **Database Indexes** - insight_type, completed_at for performance
- **P90 Metrics** - P90 time-to-insight included in response

**Import:**
```python
from app.services.dashboard import (
    DashboardOrchestrator,
    DashboardMetricsService,
    ProjectHealthService,
    QuickActionsService,
    InsightTraceabilityService,
    UsageTrackingService,
    NotificationService,
)
```

**API Endpoints:**
```python
GET /dashboard/overview                   # 8 KPI cards
GET /dashboard/quick-actions              # Recommended actions
GET /dashboard/projects/active            # Active projects + health
GET /dashboard/analytics/weekly           # Weekly trend chart
GET /dashboard/analytics/insights         # Top concepts + sentiment + types
GET /dashboard/insights/latest            # Latest insights
GET /dashboard/health/blockers            # Health summary + blockers
GET /dashboard/usage                      # Token usage + budget
GET /dashboard/notifications              # Notifications list
POST /dashboard/actions/{id}/execute      # Execute action
POST /dashboard/notifications/{id}/read   # Mark as read
```

**Performance:**
- Caching: 30-60s Redis TTL
- N+1 Optimization: 21 queries → 3 queries
- Indexes: insight_type, completed_at

**Testing:**
- 12 test cases (9 Phase 1 + 3 Phase 2)
- Coverage: insight_types, filters, budget_limit
