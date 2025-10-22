# Struktura Serwisów

**Ostatnia aktualizacja:** 2025-10-20
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

## 📦 Nowa Centralizacja (2025-10-20)

### Prompty → `app/core/prompts/`
- `persona_prompts.py` - JTBD, segment, brief, uniqueness
- `focus_group_prompts.py` - Persona responses, summaries
- `rag_prompts.py` - Cypher, Graph RAG
- `system_prompts.py` - Wspólne prompty

### Stałe → `app/core/constants/`
- `polish.py` - POLISH_* (imiona, miasta, zawody, wartości, itp.)
- `personas.py` - DEFAULT_* dla cech person (np. wartości, style komunikacji)

**Import:**
```python
from app.core.prompts.persona_prompts import JTBD_ANALYSIS_PROMPT_TEMPLATE
from app.core.constants.polish import POLISH_MALE_NAMES
```
