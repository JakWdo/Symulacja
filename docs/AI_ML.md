# Architektura AI/ML i RAG - Sight Platform

**Ostatnia aktualizacja:** 2025-11-03
**Wersja:** 2.1
**Autor:** AI/ML Engineering Team

---

## Spis Treści

1. [Przegląd Architektury](#przegląd-architektury)
2. [Model Selection Strategy](#model-selection-strategy)
3. [LLM Infrastructure](#llm-infrastructure)
4. [RAG System Architecture](#rag-system-architecture)
5. [Prompt Engineering](#prompt-engineering)
6. [Performance Optimizations](#performance-optimizations)
7. [Token Usage & Cost Management](#token-usage--cost-management)
8. [Monitoring & Observability](#monitoring--observability)

---

## Przegląd Architektury

System AI/ML w platformie Sight wykorzystuje **Google Gemini 2.5** (Flash i Pro) do generowania realistycznych person oraz symulacji grup fokusowych. Architektura oparta jest na trzech filarach:

1. **LLM Orchestration Layer** - Zarządzanie wywołaniami modeli językowych z retry logic
2. **Hybrid RAG System** - Wyszukiwanie wektorowe + słownikowe + grafowe dla polskiego kontekstu
3. **Event Sourcing** - Immutable log wszystkich interakcji AI dla audytu i reprodukowalności

### Architektura Wysokiego Poziomu

```
┌─────────────────────────────────────────────────────────────────┐
│                    SIGHT AI/ML ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Persona     │    │ Focus Group  │    │   Survey     │     │
│  │ Generation   │    │  Discussion  │    │  Response    │     │
│  │ Gemini Flash │    │ Gemini Flash │    │ Gemini Flash │     │
│  │ temp=0.9     │    │ temp=0.8     │    │ temp=0.7     │     │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │
│         │                   │                    │              │
│         └───────────────────┼────────────────────┘              │
│                             ↓                                   │
│              ┌──────────────────────────┐                       │
│              │   LLM Abstraction Layer  │                       │
│              │  (LangChain + Retry)     │                       │
│              └──────────────────────────┘                       │
│                             ↓                                   │
│         ┌───────────────────┴─────────────────────┐            │
│         ↓                                          ↓            │
│  ┌─────────────┐                         ┌─────────────┐       │
│  │  Hybrid RAG │                         │  Graph RAG  │       │
│  │  (Vector +  │                         │  (Neo4j)    │       │
│  │  Keyword)   │                         │             │       │
│  └─────────────┘                         └─────────────┘       │
│         ↓                                          ↓            │
│  ┌─────────────────────────────────────────────────────┐       │
│  │            Usage Tracking & Cost Monitoring         │       │
│  │       (Tokens, Cost, Latency, Error Rate)           │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Główne Komponenty

**Service Layer** (`app/services/`) - Logika biznesowa zorganizowana według domeny:
- `personas/` - Generacja person, orkiestracja, analiza JTBD
- `focus_groups/` - Zarządzanie dyskusjami, podsumowania, pamięć konwersacyjna
- `surveys/` - Generacja odpowiedzi na ankiety
- `rag/` - Hybrid search, graph transformations, zarządzanie dokumentami
- `shared/` - Współdzielone klienty LLM, narzędzia

**Configuration Layer** (`config/`) - Wszystkie prompty, modele i ustawienia w YAML:
- `models.yaml` - Rejestr modeli z fallback chain
- `prompts/` - 25+ promptów zorganizowanych według domeny
- `rag/retrieval.yaml` - Konfiguracja chunking, hybrid search, reranking

---

## Model Selection Strategy

**ZASADA:** Używaj najtańszego modelu, który spełnia wymagania jakościowe.

### Gemini 2.5 Flash

**Przypadki użycia:** 90% operacji - generacja person, odpowiedzi w grupach fokusowych, odpowiedzi ankietowe

**Parametry:**
- Temperature: 0.7-0.9 (kreatywność vs spójność)
- Max tokens: 2000-6000
- Timeout: 30-90s

**Performance:**
- Koszt: $0.075 / 1M input tokens, $0.30 / 1M output tokens
- Latencja: 1-3s per request
- Throughput: ~20 równoległych wywołań (asyncio.gather)

### Gemini 2.5 Pro

**Przypadki użycia:** 10% operacji - orkiestracja person, analiza JTBD, podsumowania grup fokusowych

**Parametry:**
- Temperature: 0.2-0.4 (analityczne zadania)
- Max tokens: 4000-8000
- Timeout: 90-120s

**Performance:**
- Koszt: $1.25 / 1M input tokens, $5.00 / 1M output tokens (17x drożej!)
- Latencja: 3-5s per request
- Kiedy użyć: Complex reasoning, długie konteksty (>8k tokens), wysokie wymagania jakościowe

### Model Registry (`config/models.yaml`)

Centralna konfiguracja z fallback chain:
1. Domain-specific override (np. `domains.personas.orchestration`)
2. Domain default (np. `domains.personas.generation`)
3. Global default (`defaults.chat`)

**Przykład użycia:**
```python
from config import models
from app.services.shared.clients import build_chat_model

# Pobierz konfigurację z fallback chain
model_config = models.get("personas", "generation")
# Result: {model: "gemini-2.5-flash", temperature: 0.9, ...}

# Zbuduj model z automatic retry logic
llm = build_chat_model(**model_config.params)

# Wywołaj model (async)
response = await llm.ainvoke(messages)
```

---

## LLM Infrastructure

### LangChain Abstraction Layer

**Lokalizacja:** `app/services/shared/clients.py`

**Korzyści:**
1. **Unified Interface** - Jedna funkcja `build_chat_model()` dla wszystkich serwisów
2. **Automatic Retry** - Exponential backoff dla rate limits (1s, 2s, 4s)
3. **Provider Flexibility** - Łatwa migracja Gemini → OpenAI → Anthropic
4. **Structured Outputs** - Pydantic models z walidacją
5. **Token Tracking** - Automatyczne logowanie usage_metadata

### Error Handling & Graceful Degradation

**Exponential Backoff:**
```python
# LangChain automatic retry dla ResourceExhausted (rate limits)
llm = build_chat_model(max_retries=3)
# Retry 1: 1s, Retry 2: 2s, Retry 3: 4s
```

**Graceful Degradation:**
- RAG failuje → generuj personę bez kontekstu
- Graph RAG timeout → użyj tylko vector search
- LLM failuje → fallback response (dla grup fokusowych)

---

## RAG System Architecture

### Dual-Source Retrieval Strategy

System RAG łączy dwa komplementarne źródła kontekstu:

1. **Hybrid Search** (~500ms) - Szybkie wyszukiwanie chunków tekstowych
   - Vector search: Embeddingi Gemini (768 dim) + cosine similarity
   - Keyword search: Neo4j fulltext index (Lucene)
   - RRF fusion: Reciprocal rank fusion dla balansowania wyników

2. **Graph RAG** (~1500ms) - Strukturalna wiedza z grafu
   - LLM-powered Cypher query generation
   - 4 typy węzłów: Wskaźnik, Obserwacja, Trend, Demografia
   - Bogate metadane: streszczenie, kluczowe_fakty, pewność, okres_czasu

```
Query: "kobieta, 25-34, wyższe, Warszawa"
         ↓
    ┌────────────────────────────────┐
    │   PARALLEL RETRIEVAL (~2s)     │
    ├────────────────────────────────┤
    │  Hybrid Search  │  Graph RAG   │
    │  8 chunks       │  Graph nodes │
    └────────────────────────────────┘
                 ↓
     ┌───────────────────────┐
     │ UNIFIED CONTEXT       │
     │ 8000 chars max        │
     │ Graph + Enriched      │
     │ chunks                │
     └───────────────────────┘
```

### Hybrid Search Implementation

**Lokalizacja:** `app/services/rag/rag_hybrid_search_service.py`

#### 1. Vector Search (Semantic)
- **Embeddings:** Google Gemini `models/gemini-embedding-001` (768 dimensions)
- **Index:** Neo4j Vector Index (HNSW algorithm)
- **Distance:** Cosine similarity
- **Performance:** ~200ms for top-8

#### 2. Keyword Search (Lexical)
- **Index:** Neo4j Fulltext (Lucene-based)
- **Fields:** `text` content w węzłach `RAGChunk`
- **Performance:** ~100ms for top-8

#### 3. RRF Fusion
**Formula:** `score = 1 / (k + rank + 1)` dla każdego źródła (k=60)

**Korzyści:** Balansuje semantic recall i lexical precision

```python
def rrf_fusion(vector_results, keyword_results, k=60):
    scores = {}
    # Vector contribution
    for rank, (doc, _) in enumerate(vector_results):
        scores[hash(doc)] = 1.0 / (k + rank + 1)
    # Keyword contribution
    for rank, (doc, _) in enumerate(keyword_results):
        scores[hash(doc)] = scores.get(hash(doc), 0) + 1.0 / (k + rank + 1)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

#### 4. Cross-Encoder Reranking (Opcjonalny)
- **Model:** `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Performance:** ~100-150ms dla 10 candidates
- **Configuration:** `rag.retrieval.reranking.enabled: true`

### Graph RAG Implementation

**Lokalizacja:** `app/services/rag/rag_graph_service.py`

#### Node Types
- **Wskaźnik:** Metryki, statystyki z wielkością i pewnością
- **Obserwacja:** Fakty, przyczyny, skutki
- **Trend:** Zmiany w czasie z okresem czasu
- **Demografia:** Grupy demograficzne z charakterystyką

#### Node Properties
- `streszczenie` - Jednozdaniowe podsumowanie (WYMAGANE)
- `kluczowe_fakty` - Max 3 kluczowe fakty
- `skala` - Wartość z jednostką (tylko Wskaźnik)
- `pewnosc` - wysoka / średnia / niska
- `okres_czasu` - Zakres czasowy (np. "2019-2023")
- `doc_id`, `chunk_index` - Metadane źródła

#### Graph Query Strategy

**Cypher Query Pattern (Neo4j 5.x+ CALL subqueries):**
```cypher
// Wskaźniki (top 3, preferuj wysoką pewność)
CALL () {
    MATCH (ind:Wskaznik)
    WHERE ANY(term IN $search_terms WHERE
        toLower(ind.streszczenie) CONTAINS toLower(term)
    )
    RETURN ind
    ORDER BY
        CASE ind.pewnosc
            WHEN 'wysoka' THEN 0
            WHEN 'srednia' THEN 1
            ELSE 2
        END
    LIMIT 3
}
// Analogicznie: Obserwacje (3), Trendy (2), Demografia (2)
RETURN indicators + observations + trends + demographics
```

**Performance:** <5s per query (z TEXT indexes), timeout 10s

#### Graph Context Formatting

**Przykład:**
```
=== STRUKTURALNA WIEDZA Z GRAFU WIEDZY ===

📊 WSKAŹNIKI DEMOGRAFICZNE:
• 78.4% zatrudnienia w grupie 25-34 lata (2023)
  Wielkość: 78.4%
  Pewność: wysoka
  Kluczowe fakty: Najwyższa stopa wśród grup wiekowych

📈 TRENDY:
• Wzrost zatrudnienia kobiet w IT o 23% (2019-2023)
  Okres: 2019-2023
  Kluczowe fakty: Szczególnie w Warszawie i Krakowie
```

### Unified Context Assembly

**Strategia:** Chunk enrichment

1. **Format graph context** - Graph nodes → czytelny tekst
2. **Find related nodes** - Matching: doc_id, keywords
3. **Enrich chunks** - Max 2 wskaźniki, 2 obserwacje, 1 trend per chunk
4. **Assemble** - Graph context na początku, enriched chunks poniżej
5. **Truncate** - Limit do max_context_chars (8000)

**Metryki:**
- Enriched chunks: ~40-60% chunków ma powiązane graph nodes
- Context size: ~6000-8000 chars
- Improvement: +15% persona realism score (user eval)

### Redis Caching Strategy

#### Hybrid Search Cache
- **Key:** `hybrid_search:{query_hash}:{top_k}`
- **TTL:** 7 dni
- **Hit rate:** 70-90%
- **Performance:** Cache hit <50ms vs miss ~500ms

#### Graph RAG Cache
- **Key:** `graph_context:{age}:{edu}:{loc}:{gender}`
- **TTL:** 7 dni
- **Hit rate:** 80-95%
- **Performance:** Cache hit <50ms vs miss ~1500ms

**Przykład:**
```python
cache_key = f"graph_context:{age}:{edu}:{loc}:{gender}"
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# Cache miss - execute query
nodes = await graph_store.query(cypher_query)
await redis.setex(cache_key, 604800, json.dumps(nodes))
```

---

## Prompt Engineering

### Centralized Prompt Management

**Lokalizacja:** `config/prompts/`

**Struktura:**
```
config/prompts/
├── personas/         # 7 promptów
├── focus_groups/     # 2 prompty
├── surveys/          # 4 prompty
├── rag/              # 2 prompty
└── system/           # 10 promptów systemowych
```

**Łącznie:** 25 promptów

### Prompt Template Format

```yaml
id: "personas.generation"
version: "1.0.0"
description: "Generacja syntetycznej persony"
model: "gemini-2.5-flash"
temperature: 0.9
messages:
  - role: system
    content: |
      Jesteś ekspertem generacji person dla polskiego rynku...
  - role: user
    content: |
      Wygeneruj personę: ${age}, ${gender}, ${education}
```

**Jinja2 Delimiters:** `${variable}` (kompatybilność z Cypher queries)

### Key Prompt Patterns

#### 1. Persona Generation (Flash, temp=0.9)

**Challenge:** Generuj UNIKALNE, RÓŻNORODNE persony w ramach segmentu

**Solution:**
- Persona seed: Losowy seed per persona (`#${seed}`)
- Explicit diversity: "Każda persona MUSI mieć RÓŻNĄ historię"
- Few-shot example: Bogaty przykład (400-600 słów background_story)
- RAG integration: Kontekst jako TŁO (nie cytuj statystyk!)

#### 2. Orchestration (Pro, temp=0.3)

**Challenge:** Analityczna segmentacja + długie edukacyjne briefe

**Solution:**
- System prompt: Polish society expert
- Graph context: Insights z Neo4j jako faktyczne dane
- Długie briefe: 900-1200 znaków per segment
- JSON output: Pydantic validation

**Output:**
```json
{
  "total_personas": 20,
  "groups": [
    {
      "segment_name": "Młodzi Prekariusze",
      "allocation": 6,
      "segment_brief": "Kim są młodzi prekariusze? [900-1200 znaków]",
      "reasoning": "Dlaczego 6 person..."
    }
  ]
}
```

#### 3. Focus Group Response (Flash, temp=0.8)

**Challenge:** Naturalne odpowiedzi 2-4 zdania

**Solution:**
- Pełny persona context: Demografia, wartości, background_story
- Conversation history: Top 3 previous responses (RAG z event sourcing)
- Natural language: "Respond naturally as this person would"

#### 4. JTBD Analysis (Pro, temp=0.25)

**Challenge:** Deterministyczna ekstrakcja Jobs-to-be-Done

**Solution:**
- Very low temperature (0.25)
- Few-shot examples: 2 kompletne przykłady
- Structured output: Pydantic (job, desired_outcome, pains)
- RAG integration: Polish market context

**Output:**
```json
{
  "jobs_to_be_done": [
    {
      "job": "Znaleźć stabilną pracę z możliwością rozwoju",
      "job_type": "functional",
      "frequency": "ongoing"
    }
  ],
  "desired_outcomes": [...],
  "pains": [...]
}
```

### Prompt Validation

**Script:** `scripts/config_validate.py`

```bash
# Waliduj wszystkie prompty
python scripts/config_validate.py

# Sprawdź placeholdery
python scripts/config_validate.py --check-placeholders

# Auto-bump wersji
python scripts/config_validate.py --auto-bump
```

**Versioning:** Semantic versioning (major.minor.patch)

---

## Performance Optimizations

### 1. Parallel LLM Calls

**Problem:** Sequential calls = 20 person × 3s = 60s

**Solution:** Asyncio.gather

```python
# ❌ Wolne (sequential)
personas = []
for demographic in demographics:
    persona = await generate_persona(demographic)
    personas.append(persona)

# ✅ Szybkie (parallel)
tasks = [generate_persona(d) for d in demographics]
personas = await asyncio.gather(*tasks)
# Total: ~5s (limited by Gemini API rate)
```

**Rate Limiting:** Semaphore

```python
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def generate_with_limit(demographic):
    async with semaphore:
        return await generate_persona(demographic)
```

### 2. Segment Caching (Redis)

**Problem:** Identyczne segment briefe generowane wielokrotnie

**Solution:** Redis cache z 7-day TTL

**Metryki:**
- Hit rate: ~85%
- Speedup: 3x faster (cache hit <50ms vs generation ~1500ms)
- Token savings: 60% redukcja input tokens

### 3. Prompt Compression

**Przed:**
```python
prompt = f"""
You are a persona generation expert specializing in creating
realistic, statistically representative personas...
"""
# ~500 tokens
```

**Po:**
```python
prompt = f"""
Expert: Syntetyczne persony dla polskiego rynku.
PROFIL: Wiek: {age} | Płeć: {gender}
"""
# ~200 tokens (60% redukcja)
```

**Savings:** 300 tokens × 20 person = 6000 tokens = $0.00045 saved per batch

### 4. Batch Processing

**Embeddings:**
```python
# ❌ Sequential
embeddings = []
for chunk in chunks:
    emb = await embeddings_model.aembed_query(chunk.text)
    embeddings.append(emb)

# ✅ Batch
texts = [chunk.text for chunk in chunks]
embeddings = await embeddings_model.aembed_documents(texts)
# Gemini: batch size 100 (5-10x faster)
```

---

## Token Usage & Cost Management

### Token Tracking Architecture

**Lokalizacja:** `app/services/dashboard/usage_logging.py`

**Flow:**
```
LLM Call → Extract usage_metadata → Log to DB (async) → Dashboard
```

**Extraction:**
```python
response = await llm.ainvoke(messages)
usage = response.response_metadata.get("usage_metadata")
# Gemini format:
# {
#   "prompt_token_count": 1234,
#   "candidates_token_count": 567,
#   "total_token_count": 1801
# }

input_tokens = usage.get("prompt_token_count")
output_tokens = usage.get("candidates_token_count")
```

**Async Logging (Non-blocking):**
```python
asyncio.create_task(
    log_usage(
        user_id=user_id,
        operation="persona_generation",
        model="gemini-2.5-flash",
        input_tokens=1234,
        output_tokens=567
    )
)
```

### Cost Calculation

**Pricing:** `config/pricing.yaml`

```yaml
gemini-2.5-flash:
  input_price_per_million: 0.075
  output_price_per_million: 0.30

gemini-2.5-pro:
  input_price_per_million: 1.25
  output_price_per_million: 5.00
```

**Formula:**
```python
input_cost = (input_tokens / 1_000_000) * input_price
output_cost = (output_tokens / 1_000_000) * output_price
total_cost = input_cost + output_cost
```

**Przykład:** 20 person
```
Input: 40,000 tokens
Output: 30,000 tokens

Gemini Flash:
  $0.003 (input) + $0.009 (output) = $0.012

Gemini Pro:
  $0.05 (input) + $0.15 (output) = $0.20 (17x drożej!)
```

### Cost Optimization Strategies

#### 1. Model Selection
- **Rule:** Zawsze Flash chyba że Pro absolutnie konieczny
- **Savings:** 17x cheaper
- **Flash:** 90% operacji
- **Pro:** 10% operacji (orchestration, JTBD, summaries)

#### 2. Caching
- **Redis cache:** Segment briefe, graph context
- **Hit rate:** 70-90%
- **Savings:** $0.002 per cached query

#### 3. Token Budgeting
```python
budget_service = BudgetService(db)
remaining = await budget_service.get_remaining_budget(user_id)

if remaining < estimated_cost:
    raise BudgetExceededError(
        f"Insufficient budget. Remaining: ${remaining:.2f}"
    )
```

---

## Monitoring & Observability

### Target Performance Metrics (SLA)

| Operation | Target P95 | Current Avg | Status |
|-----------|-----------|-------------|--------|
| **Persona Generation** (20 personas) | <60s | ~45s | ✅ Met |
| **Focus Group** (20 × 4 questions) | <3min | ~2min | ✅ Met |
| **Hybrid Search** (vector + keyword + RRF) | <350ms | ~280ms | ✅ Met |
| **Graph RAG Query** | <5s | ~3s | ✅ Met |
| **API Response** (P90) | <500ms | ~420ms | ✅ Met |

### Key Metrics to Track

**LLM Performance:**
- Tokens per operation (input/output)
- Cost per operation ($USD)
- Latency (p50, p90, p95, p99)
- Error rate (% failed calls)
- Retry rate (% requiring retry)

**RAG Performance:**
- Cache hit rate (hybrid, graph)
- Retrieval latency (vector, keyword, graph)
- Context size (chars, tokens)
- Relevance score (user feedback)

**Quality Metrics:**
- Persona quality score (0-100)
- Demographic accuracy (chi-square p-value)
- Consistency score (% passing checks)
- Hallucination rate (% with uncited facts)

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Log LLM call
logger.info(
    "LLM generation completed",
    extra={
        "operation": "persona_generation",
        "model": "gemini-2.5-flash",
        "input_tokens": 1234,
        "output_tokens": 567,
        "latency_ms": 2800,
        "cost_usd": 0.00026,
        "user_id": str(user_id),
        "project_id": str(project_id)
    }
)
```

---

## Appendix: Quick Reference

### Kluczowe Pliki

**Backend:**
- `app/services/shared/clients.py` - LLM abstraction layer
- `app/services/rag/rag_hybrid_search_service.py` - Hybrid search
- `app/services/rag/rag_graph_service.py` - Graph RAG
- `app/services/personas/persona_generator_langchain.py` - Generacja person
- `app/services/dashboard/usage_logging.py` - Token tracking

**Configuration:**
- `config/models.yaml` - Rejestr modeli LLM
- `config/prompts/` - 25 promptów YAML
- `config/rag/retrieval.yaml` - Konfiguracja RAG
- `config/pricing.yaml` - Ceny modeli

**Dokumentacja:**
- `config/README.md` - Przewodnik po systemie konfiguracji
- `config/PROMPTS_INDEX.md` - Katalog wszystkich promptów
- `docs/RAG.md` - Architektura RAG (szczegóły)
- `docs/TESTING.md` - Organizacja testów

### Detailed Documentation Reference

**Szczegółowe dokumenty dostępne w `docs/architecture/`:**
- `ai_ml.md` - Pełna wersja z dodatkowymi szczegółami (1370 linii)
  - Szczegółowe benchmarki performance
  - Rozszerzona sekcja Persona Details View
  - Długie przykłady kodu i promptów
  - Roadmap Q1-Q4 2025

---

**Autorzy:** AI/ML Engineering Team
**Kontakt:** Slack #ai-ml-engineering
**Ostatnia aktualizacja:** 2025-11-03
