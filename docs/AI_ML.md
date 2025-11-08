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

## LangGraph Integration & Study Designer

### Przegląd

**LangGraph** to framework state machine'ów do orchestracji złożonych przepływów konwersacyjnych z LLM. W Sight używamy LangGraph w **Study Designer Chat** - systemie konwersacyjnego projektowania badań, który prowadzi użytkownika przez wieloetapowy proces definiowania badania UX.

**Dlaczego LangGraph?**
- **State persistence** - TypedDict state zapisywany w PostgreSQL (JSONB)
- **Conditional routing** - Węzły decydują o następnym kroku na podstawie danych
- **Loop-back logic** - Możliwość powrotu do poprzednich etapów gdy dane niekompletne
- **Message history** - Pełna historia konwersacji user ↔ assistant
- **Separation of concerns** - Każdy node ma jedną odpowiedzialność (SRP)

### Architektura Study Designer

```
┌─────────────────────────────────────────────────┐
│           LangGraph StateGraph                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  START → welcome → gather_goal ────┐            │
│                      ↑              ↓            │
│                      └──(loop)── define_audience│
│                                     ↓            │
│                              select_method      │
│                                     ↓            │
│                             configure_details   │
│                                     ↓            │
│                              generate_plan      │
│                                     ↓            │
│                              await_approval     │
│                                     ↓            │
│                                   END            │
└─────────────────────────────────────────────────┘
```

**7 Node Types:**

1. **welcome** (static) - Wiadomość powitalna
2. **gather_goal** (LLM) - Ekstrakcja celu badania
3. **define_audience** (LLM) - Definicja grupy docelowej
4. **select_method** (LLM) - Wybór metody (personas/focus_group/survey/mixed)
5. **configure_details** (LLM) - Szczegóły konfiguracji
6. **generate_plan** (LLM) - Generacja planu badania (Markdown)
7. **await_approval** (static) - Oczekiwanie na zatwierdzenie

### State Schema (TypedDict)

```python
from typing import TypedDict, NotRequired, Literal

class ConversationState(TypedDict):
    session_id: str
    user_id: str
    messages: list[dict[str, str]]  # [{"role": "user|assistant|system", "content": "..."}]
    current_stage: Literal["welcome", "gather_goal", "define_audience", ...]

    # Optional fields (populated during conversation)
    study_goal: NotRequired[str | None]
    target_audience: NotRequired[dict | None]
    research_method: NotRequired[Literal["personas", "focus_group", "survey", "mixed"] | None]
    configuration: NotRequired[dict | None]
    generated_plan: NotRequired[dict | None]
    plan_approved: NotRequired[bool]
```

**Serialization:**
- State zapisywany jako JSON w `study_designer_sessions.conversation_state` (JSONB column)
- Datetime i UUID konwertowane do string przed zapisem
- Deserializacja odtwarza TypedDict z DB JSON

### Node Implementation Pattern

**Przykład: gather_goal node**

```python
async def gather_goal_node(state: ConversationState) -> ConversationState:
    """Ekstraktuje cel badania z wiadomości użytkownika."""

    # 1. Pobierz ostatnią wiadomość użytkownika
    user_message = get_last_user_message(state)
    if not user_message:
        return state  # Brak wiadomości - zostań w obecnym stage

    # 2. Przygotuj prompt z kontekstem
    template = prompts.get("study_designer.gather_goal")
    prompt_text = template.render(user_message=user_message)

    # 3. Wywołaj LLM (Gemini 2.5 Flash, temp=0.8)
    model_config = models.get("study_designer", "question_generation")
    llm = build_chat_model(**model_config.params)
    response = await llm.ainvoke(prompt_text)

    # 4. Parsuj strukturowany JSON output
    llm_output = parse_llm_json_response(response.content)
    # Expected: {goal_extracted: bool, goal: str|null, confidence: str,
    #            follow_up_question: str|null, assistant_message: str}

    # 5. Zaktualizuj state na podstawie wyniku
    if llm_output.get("goal_extracted") and llm_output.get("goal"):
        state["study_goal"] = llm_output["goal"]
        state["current_stage"] = "define_audience"  # Sukces - idź dalej
    else:
        state["current_stage"] = "gather_goal"  # Loop-back - zadaj kolejne pytanie

    # 6. Dodaj odpowiedź asystenta do historii
    state["messages"].append({
        "role": "assistant",
        "content": llm_output["assistant_message"]
    })

    return state
```

**Kluczowe wzorce:**
- **Conditional stage transition** - Node ustawia `current_stage` aby kontrolować routing
- **Loop-back pattern** - Jeśli dane niekompletne, node pozostawia stage bez zmian
- **Structured JSON output** - LLM zwraca JSON z predefiniowanymi polami
- **State mutation** - Node modyfikuje state in-place i zwraca zaktualizowany

### LLM Configuration per Stage

**config/models.yaml:**

```yaml
domains:
  study_designer:
    question_generation:  # gather_goal, define_audience, select_method
      model: "gemini-2.5-flash"
      temperature: 0.8  # Wyższa dla kreatywnych follow-up questions
      max_tokens: 2000
      timeout: 30
      retries: 3

    plan_generation:  # generate_plan
      model: "gemini-2.5-flash"
      temperature: 0.3  # Niższa dla strukturowanego outputu
      max_tokens: 6000
      timeout: 60
      retries: 3
```

**Dlaczego różne temperatury?**
- **Wysoka (0.7-0.8):** Pytania dostosowane do kontekstu, kreatywne follow-upy
- **Średnia (0.5-0.6):** Wybór opcji z wyjaśnieniem
- **Niska (0.3-0.4):** Strukturowany output (plan Markdown, estymacje)

### Prompts (Jinja2 Templates)

**5 Promptów Study Designer** w `config/prompts/study_designer/`:

**1. gather_goal.yaml** - Ekstrakcja celu badania
```yaml
id: study_designer.gather_goal
version: "1.0.0"
messages:
  - role: system
    content: |
      Jesteś ekspertem UX researcher. Twoim zadaniem jest zrozumienie
      celu badania poprzez analizę odpowiedzi i zadawanie pytań.

      FORMAT ODPOWIEDZI - ZAWSZE JSON:
      {
        "goal_extracted": true/false,
        "goal": "Pełny wyekstraktowany cel lub null",
        "confidence": "high"|"medium"|"low",
        "follow_up_question": "Pytanie do użytkownika lub null",
        "assistant_message": "Pełna odpowiedź dla użytkownika"
      }

      KRYTERIA SUKCESU:
      - Cel konkretny (nie "zrobić badanie" ale "zrozumieć porzucanie koszyka")
      - Cel mierzalny (można zaprojektować badanie wokół niego)
      - Cel biznesowy (rozwiązuje problem lub odpowiada na pytanie)

  - role: user
    content: ${user_message}
```

**2. define_audience.yaml** - Definicja grupy docelowej
```yaml
id: study_designer.define_audience
version: "1.0.0"
messages:
  - role: system
    content: |
      Ekstraktuj demografię grupy docelowej. Pytaj o:
      - Wiek (range lub konkretne grupy)
      - Płeć (jeśli istotne)
      - Lokalizacja (kraj, miasto, region)
      - Zawód / branża
      - Psychografia (postawy, zachowania, wartości)

      JSON OUTPUT:
      {
        "audience_defined": true/false,
        "target_audience": {
          "age_range": "25-40",
          "gender": "all"|"male"|"female"|"other",
          "location": "Polska, miasta >100k",
          "occupation": "IT professionals",
          "psychographics": "Early adopters, tech-savvy"
        },
        "follow_up_question": null,
        "assistant_message": "..."
      }
```

**3. generate_plan.yaml** - Generacja kompletnego planu
```yaml
id: study_designer.generate_plan
version: "1.0.0"
messages:
  - role: system
    content: |
      Wygeneruj kompletny plan badania w formacie Markdown.

      INPUT CONTEXT:
      - Cel: ${study_goal}
      - Grupa docelowa: ${target_audience}
      - Metoda: ${research_method}
      - Konfiguracja: ${configuration}

      JSON OUTPUT:
      {
        "markdown_summary": "# Plan Badania\n\n## Cel\n...",
        "estimated_time_seconds": 1200,  // Total execution time
        "estimated_cost_usd": 8.50,
        "execution_steps": [
          {"type": "personas_generation", "config": {...}},
          {"type": "focus_group_discussion", "config": {...}}
        ]
      }

      PLAN STRUCTURE (Markdown):
      # Plan Badania UX

      ## 1. Cel Badania
      ${study_goal}

      ## 2. Grupa Docelowa
      (demografia)

      ## 3. Metoda Badawcza
      ${research_method} - wyjaśnienie dlaczego

      ## 4. Szczegóły Wykonania
      - Liczba person/uczestników
      - Liczba pytań/zadań
      - Timeline

      ## 5. Oczekiwane Wnioski
      Co dowiemy się z tego badania?

      ## 6. Next Steps
      Jak wykorzystać wyniki?
```

### JSON Parsing with Fallbacks

**Robust parsing strategy** (3-level fallback):

```python
def parse_llm_json_response(content: str) -> dict:
    """Parsuje JSON z LLM response z multiple fallback strategies."""

    # Strategy 1: Direct JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code blocks
    match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find first {...} block
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: Return error structure
    return {
        "error": "Failed to parse JSON",
        "raw_content": content
    }
```

**Dlaczego potrzebne?**
- LLM czasami opakowuje JSON w markdown (` ```json ... ``` `)
- LLM dodaje dodatkowy tekst przed/po JSON
- Fallback zapewnia graceful degradation

### Conditional Routing Implementation

```python
class ConversationStateMachine:
    def __init__(self):
        workflow = StateGraph(ConversationState)

        # Add all nodes
        workflow.add_node("welcome", welcome_node)
        workflow.add_node("gather_goal", gather_goal_node)
        workflow.add_node("define_audience", define_audience_node)
        # ... etc

        # Static edges (always proceed)
        workflow.add_edge("welcome", "gather_goal")

        # Conditional edges (routing based on state)
        workflow.add_conditional_edges(
            "gather_goal",
            self._route_from_gather_goal,
            {
                "define_audience": "define_audience",  # Success path
                "gather_goal": "gather_goal"  # Loop-back path
            }
        )

        workflow.set_entry_point("welcome")
        self.graph = workflow.compile()

    def _route_from_gather_goal(self, state: ConversationState) -> str:
        """Routing logic: check current_stage set by node."""
        if state["current_stage"] == "define_audience":
            return "define_audience"  # Goal extracted - proceed
        return "gather_goal"  # Goal unclear - ask again
```

**Key Pattern:**
- Node ustawia `current_stage` w state
- Routing function sprawdza `current_stage` i zwraca nazwę następnego node
- LangGraph automatycznie wywołuje wskazany node

### State Persistence Strategy

**Database:** `study_designer_sessions` table (PostgreSQL)

```sql
CREATE TABLE study_designer_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    conversation_state JSONB NOT NULL,  -- Complete LangGraph state
    status VARCHAR(50) DEFAULT 'active',
    current_stage VARCHAR(50) DEFAULT 'welcome',
    generated_plan JSONB,  -- Cached from state for indexing
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for user queries
CREATE INDEX idx_sessions_user_status ON study_designer_sessions(user_id, status);

-- GIN index for JSONB queries (optional)
CREATE INDEX idx_sessions_state ON study_designer_sessions USING GIN(conversation_state);
```

**Serialization Functions:**

```python
def serialize_state(state: ConversationState) -> dict:
    """Convert TypedDict to JSON-serializable dict."""
    return {
        "session_id": state["session_id"],
        "user_id": state["user_id"],
        "messages": state["messages"],
        "current_stage": state["current_stage"],
        **{k: v for k, v in state.items() if k not in ["session_id", "user_id", "messages", "current_stage"]}
    }

def deserialize_state(data: dict) -> ConversationState:
    """Convert DB JSON back to TypedDict."""
    return ConversationState(**data)
```

### Performance Metrics

| Metryka | Target | Actual | Optimization |
|---------|--------|--------|--------------|
| Session init | < 2s | ~1.5s | Static welcome message |
| Message processing (LLM) | < 5s | ~3-4s | Gemini Flash (fast model) |
| Plan generation | < 8s | ~6s | Concurrent LLM calls |
| State save to DB | < 100ms | ~50ms | JSONB native format |
| State load from DB | < 100ms | ~40ms | Indexed query |

**Token Usage per Stage:**

| Stage | Avg Input Tokens | Avg Output Tokens | Cost per Stage |
|-------|------------------|-------------------|----------------|
| gather_goal | 150 | 100 | $0.04 |
| define_audience | 200 | 120 | $0.05 |
| select_method | 250 | 180 | $0.06 |
| configure_details | 300 | 150 | $0.07 |
| generate_plan | 500 | 800 | $0.28 |
| **Total per session** | **~1400** | **~1350** | **~$0.50** |

### Error Handling & Resilience

**LLM Failures:**
```python
try:
    response = await llm.ainvoke(prompt)
except Exception as e:
    logger.error(f"LLM call failed: {e}", extra={"session_id": session_id})

    # Fallback: Add error message to conversation
    state["messages"].append({
        "role": "assistant",
        "content": "Przepraszam, wystąpił problem. Spróbuj ponownie za moment."
    })

    # Don't change current_stage - allow retry
    return state
```

**State Corruption Recovery:**
```python
def validate_state(state: ConversationState) -> bool:
    """Validate state consistency."""
    required_fields = ["session_id", "user_id", "messages", "current_stage"]
    if not all(field in state for field in required_fields):
        return False

    if state["current_stage"] not in VALID_STAGES:
        return False

    # Check stage progression logic
    if state["current_stage"] == "define_audience" and not state.get("study_goal"):
        return False  # Can't be in define_audience without goal

    return True
```

### Future Enhancements

**Priority 1:**
- [ ] **Modify plan flow** - Pozwól użytkownikowi wrócić do dowolnego stage'u
- [ ] **Multi-turn clarification** - Głębsza konwersacja w ramach jednego node
- [ ] **Session templates** - Zapisuj i ponownie używaj udanych konfiguracji

**Priority 2:**
- [ ] **Voice input integration** - Web Speech API dla mówionego inputu
- [ ] **Real-time typing indicators** - Pokazuj gdy LLM "pisze"
- [ ] **Suggested responses** - Quick reply buttons na podstawie kontekstu

**Priority 3:**
- [ ] **Multi-language support** - Tłumaczenie promptów (English, German)
- [ ] **Collaborative sessions** - Wielu użytkowników w jednej sesji
- [ ] **A/B testing prompts** - Testuj różne wersje promptów

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
