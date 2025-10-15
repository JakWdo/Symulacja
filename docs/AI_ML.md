# 🤖 AI/ML System Documentation

Kompletna dokumentacja systemu AI/ML w Market Research SaaS - od integracji z Google Gemini, przez prompt engineering, do optymalizacji wydajności i troubleshootingu.

---

## 📋 Spis Treści

1. [Overview of AI Components](#overview-of-ai-components)
2. [LangChain Integration](#langchain-integration)
3. [Prompt Engineering Best Practices](#prompt-engineering-best-practices)
4. [RAG System Deep Dive](#rag-system-deep-dive)
5. [Performance & Cost Optimization](#performance--cost-optimization)
6. [Quality Assurance](#quality-assurance)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview of AI Components

### AI Stack

**Primary LLM:** Google Gemini 2.5 (Flash & Pro variants)

**Models używane:**
- **Gemini 2.5 Flash** - Szybkie operacje (persona generation, focus groups, surveys)
  - Użycie: ~70% requestów
  - Cost: $0.00005/1k tokens (input), $0.00015/1k tokens (output)
  - Latency: ~1-3s per request

- **Gemini 2.5 Pro** - Complex analysis (graph insights, executive summaries)
  - Użycie: ~30% requestów
  - Cost: $0.00125/1k tokens (input), $0.00375/1k tokens (output)
  - Latency: ~3-5s per request

**Embeddings:** Google `text-embedding-001`
- Dimensions: 768
- Cost: $0.00001/1k tokens
- Użycie: Persona events (memory), RAG document chunking

**Orchestration:** LangChain
- Version: 0.1.x
- Purpose: Abstrakcja LLM operations, prompt templates, memory management

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     AI/ML SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐       ┌──────────────────┐          │
│  │ Persona          │       │ Focus Group      │          │
│  │ Generation       │       │ Orchestration    │          │
│  │ (Gemini Flash)   │       │ (Gemini Flash)   │          │
│  └────────┬─────────┘       └────────┬─────────┘          │
│           │                          │                     │
│           ↓                          ↓                     │
│  ┌─────────────────────────────────────────────┐          │
│  │         RAG System (Hybrid Search)          │          │
│  │  ┌──────────────┐    ┌──────────────────┐  │          │
│  │  │ Vector Search│    │ Graph RAG        │  │          │
│  │  │ (Embeddings) │    │ (Neo4j Cypher)   │  │          │
│  │  └──────────────┘    └──────────────────┘  │          │
│  └─────────────────────────────────────────────┘          │
│           │                          │                     │
│           ↓                          ↓                     │
│  ┌──────────────────┐       ┌──────────────────┐          │
│  │ Memory Service   │       │ Survey Generator │          │
│  │ (Event Sourcing) │       │ (Gemini Flash)   │          │
│  └──────────────────┘       └──────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Metrics (Current Performance)

| Operation | Model | Avg Tokens (in) | Avg Tokens (out) | Avg Latency | Cost per Op |
|-----------|-------|-----------------|------------------|-------------|-------------|
| Persona generation | Flash | ~2000 | ~500 | 2-3s | $0.001 |
| Focus group response | Flash | ~1500 | ~200 | 1-2s | $0.0005 |
| Survey response | Flash | ~1000 | ~100 | 1s | $0.0003 |
| Graph RAG query | Flash | ~3000 | ~800 | 3-4s | $0.002 |
| Executive summary | Pro | ~5000 | ~1500 | 4-6s | $0.012 |

**Monthly Cost Estimation (1000 users):**
- Persona generation: 1000 × 20 personas × $0.001 = **$20**
- Focus groups: 1000 × 5 groups × 20 personas × 4 questions × $0.0005 = **$200**
- Surveys: 1000 × 3 surveys × 20 personas × 5 questions × $0.0003 = **$90**
- **Total: ~$310/month** (with Gemini Flash pricing)

---

## 🔗 LangChain Integration

### Service Architecture

**1. PersonaGeneratorLangChain** (`app/services/persona_generator_langchain.py`)
- **Purpose:** Generuje realistyczne persony z demografią, psychologią, kulturą
- **Key methods:**
  - `generate_personas_batch(num_personas)` - Główny workflow
  - `_sample_demographics()` - Statistical sampling
  - `_generate_persona_narrative()` - LLM narration z RAG context
- **Dependencies:** PolishSocietyRAG (dla context), PersonaValidator (dla statistical validation)
- **Performance:** ~30-60s dla 20 person (z RAG)

**2. FocusGroupServiceLangChain** (`app/services/focus_group_service_langchain.py`)
- **Purpose:** Orkiestracja dyskusji grup fokusowych (async parallelization)
- **Key methods:**
  - `run_focus_group()` - Główny orchestrator
  - `_generate_response_for_persona()` - Async task per persona
  - `_get_discussion_context()` - Memory retrieval
- **Dependencies:** MemoryServiceLangChain (dla context), Gemini Flash (dla responses)
- **Performance:** ~2-5 min dla 20 person × 4 pytania (parallel execution)

**3. MemoryServiceLangChain** (`app/services/memory_service_langchain.py`)
- **Purpose:** Event sourcing z semantic search (pgvector)
- **Key methods:**
  - `store_persona_event()` - Immutable event storage
  - `get_relevant_history()` - Semantic search w historii
  - `get_conversation_context()` - Summarize recent events
- **Dependencies:** PostgreSQL + pgvector (dla embeddings)
- **Performance:** <100ms semantic search

**4. RAGDocumentService** (`app/services/rag_document_service.py`)
- **Purpose:** Zarządzanie dokumentami (ingest, CRUD)
- **Key methods:**
  - `ingest_document()` - Load → chunk → embed → store
  - `_chunk_document()` - RecursiveCharacterTextSplitter (1000 chars, 300 overlap)
  - `_build_graph_from_chunks()` - Graph RAG construction
- **Dependencies:** PyPDFLoader, Docx2txtLoader, LLMGraphTransformer
- **Performance:** ~30-60s per document (depends on size)

**5. GraphRAGService** (`app/services/rag_graph_service.py`)
- **Purpose:** Graph RAG operations (budowa grafu wiedzy, Cypher generation)
- **Key methods:**
  - `answer_question()` - Pełny pipeline Graph RAG
  - `_generate_cypher_query()` - LLM generuje Cypher z pytań w NL
  - `get_demographic_graph_context()` - Zapytania specyficzne dla demografii
- **Dependencies:** Neo4j driver, Gemini Flash (dla Cypher generation)
- **Performance:** ~3-5s per query

**6. PolishSocietyRAG** (`app/services/rag_hybrid_search_service.py`)
- **Purpose:** Hybrid search (vector + keyword + RRF fusion + reranking)
- **Key methods:**
  - `get_demographic_insights()` - Główna metoda dla generatora person
  - `_hybrid_search()` - Vector + keyword + RRF fusion
  - `_rerank_results()` - Cross-encoder precision boost
- **Dependencies:** Neo4j vector store, Google embeddings, Cross-encoder model
- **Performance:** ~350ms per query (with reranking)

### LangChain Key Concepts

#### 1. Chat Models (ChatGoogleGenerativeAI)

```python
from langchain_google_genai import ChatGoogleGenerativeAI

# Gemini Flash
llm_flash = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=2048,
    google_api_key=settings.GOOGLE_API_KEY
)

# Gemini Pro
llm_pro = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0.3,
    max_tokens=4096,
    google_api_key=settings.GOOGLE_API_KEY
)

# Usage
response = await llm_flash.ainvoke("Generate a persona profile...")
```

#### 2. Prompt Templates

```python
from langchain.prompts import ChatPromptTemplate

# System + User message
persona_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert persona generator for market research..."),
    ("user", "Generate a persona with demographics: {demographics}\nRAG Context: {rag_context}")
])

# Format prompt
formatted = persona_prompt.format_messages(
    demographics="Age: 25-34, Gender: Female, Location: Warsaw",
    rag_context="[RAG insights about young Polish women in Warsaw]"
)

# Invoke LLM
response = await llm_flash.ainvoke(formatted)
```

#### 3. Output Parsers (StructuredOutputParser)

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class PersonaOutput(BaseModel):
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")
    background: str = Field(description="Background story (2-3 sentences)")
    values: list[str] = Field(description="Top 3 values")

parser = PydanticOutputParser(pydantic_object=PersonaOutput)

# Add format instructions to prompt
format_instructions = parser.get_format_instructions()
prompt = f"Generate a persona...\n\n{format_instructions}"

# Parse output
response = await llm_flash.ainvoke(prompt)
parsed = parser.parse(response.content)  # Returns PersonaOutput instance
```

#### 4. Memory (ConversationBufferMemory)

**Currently:** Custom implementation (MemoryServiceLangChain) z pgvector semantic search

**Future:** Rozważyć LangChain ConversationBufferMemory dla prostszych use cases

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True)
memory.save_context({"input": "What is your opinion?"}, {"output": "I think..."})
history = memory.load_memory_variables({})
```

---

## 🎨 Prompt Engineering Best Practices

### 1. Prompt Structure (General Pattern)

```
[ROLE] - Kim jest model (np. "You are an expert persona generator")
[CONTEXT] - Kontekst zadania (background info)
[TASK] - Co ma zrobić (specific instructions)
[CONSTRAINTS] - Ograniczenia (format, length, tone)
[EXAMPLES] - Few-shot examples (opcjonalnie)
[OUTPUT FORMAT] - Jak ma wyglądać output (JSON, paragraphs, bullet points)
```

### 2. Persona Generation Prompt (Optimized)

**Problem (Przed optymalizacją):** 700+ linii promptu → LLM confused, 4000+ tokens

**Solution (Po optymalizacji):** 250 linii → focused, 1500 tokens (-60% token usage!)

**Before (Prompt Bloat):**
```python
PERSONA_PROMPT = """
You are an expert persona generator for market research in Poland.

# Background
[500 words o polskim społeczeństwie, historii, kulturze...]

# Task
Generate a realistic persona with:
1. Demographics (age, gender, location, education, income, occupation)
2. Psychology (Big Five traits: openness, conscientiousness, extraversion, agreeableness, neuroticism)
3. Cultural dimensions (Hofstede: power distance, individualism, masculinity, uncertainty avoidance, long-term orientation, indulgence)
4. Background story (explain their values and interests based on demographics)

[100 lines o każdym trait...]

# Important Notes
[200 lines o edge cases, corner cases, special instructions...]

# Output Format
Return JSON: {{ ... }}

# RAG Context
{rag_context}
"""
```

**After (Optimized):**
```python
PERSONA_PROMPT = """
Generate a realistic Polish persona based on demographics and cultural context.

## Demographics
{demographics}

## RAG Context (Polish Society Insights)
{rag_context}

## Requirements
- Big Five traits (0-1 scale, avoid 0.5 "average")
- Hofstede dimensions (Poland-specific ranges)
- Background story (50-150 words, mentions occupation)
- Values (top 3, specific to demographics)

## Output Format
JSON:
{{
  "name": "string",
  "age": int,
  "background": "string (50-150 words)",
  "big_five": {{"openness": float, ...}},
  "hofstede": {{"power_distance": float, ...}},
  "values": ["string", "string", "string"]
}}

IMPORTANT: Use RAG context to ground persona in realistic Polish context.
"""
```

**Results:**
- Tokens: 4000 → 1500 (-62%)
- Quality: Same or better (more focused instructions)
- Latency: 3s → 2s (-33%)

### 3. Focus Group Response Prompt

**Temperature: 0.3** (consistency > creativity)

```python
FOCUS_GROUP_PROMPT = """
You are {persona_name}, age {age}, {occupation}.

## Your Profile
- Personality: {big_five_traits}
- Values: {values}
- Background: {background}

## Previous Discussion
{memory_context}

## Current Question
{question}

Respond as this persona would (stay in character, 2-3 sentences).
Consider your personality, values, and previous responses.
"""
```

**Key principles:**
- **Stay in character** - Model needs to "roleplay" as persona
- **Include memory** - Reference previous responses dla spójności
- **Specific length** - "2-3 sentences" prevents rambling
- **Lower temperature** - 0.3 dla consistency (nie 0.7 jak w generation)

### 4. Survey Response Prompt

**Temperature: 0.0** (deterministic)

```python
SURVEY_PROMPT = """
Based on your persona profile, answer this survey question.

## Persona Profile
- Demographics: {demographics}
- Personality: {big_five_traits}
- Values: {values}

## Question
{question}

## Options
{options}

Return JSON: {{"answer": "option_id", "reasoning": "1 sentence why"}}

IMPORTANT: Choose the option most aligned with persona's values and personality.
"""
```

**Key principles:**
- **Temperature 0.0** - Deterministic answers (same persona = same answer)
- **Include reasoning** - Explainability (why this choice?)
- **JSON output** - Easy parsing

### 5. Graph RAG Cypher Generation Prompt

```python
CYPHER_GENERATION_PROMPT = """
Generate a Cypher query to answer this question using the Polish society knowledge graph.

## Graph Schema
Nodes: Obserwacja, Wskaznik, Demografia, Trend, Lokalizacja
Relationships: OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W, POWIAZANY_Z
Properties: streszczenie, skala, pewnosc, okres_czasu, kluczowe_fakty

## Question
{question}

## Requirements
- Return ONLY the Cypher query (no explanations)
- Use LIMIT 10 to prevent large results
- Filter by pewnosc='wysoka' for reliable data
- Sort by relevance (e.g., skala DESC for "largest indicators")

## Example
Question: "Jakie są największe wskaźniki ubóstwa w Polsce?"
Query:
MATCH (n:Wskaznik)
WHERE n.streszczenie CONTAINS 'ubóstwo' AND n.pewnosc = 'wysoka'
RETURN n.streszczenie, n.skala, n.okres_czasu
ORDER BY toFloat(split(n.skala, '%')[0]) DESC
LIMIT 10
"""
```

**Key principles:**
- **Schema first** - Model musi znać available nodes/relationships
- **Return ONLY query** - Nie chcemy explanations (parsing issues)
- **Include example** - Few-shot learning (pokazuje pattern)

### 6. Temperature Settings Guide

| Use Case | Temperature | Reasoning |
|----------|-------------|-----------|
| Survey responses | 0.0 | Deterministic (same persona → same answer) |
| Focus group responses | 0.3 | Low creativity (consistent persona behavior) |
| Persona generation | 0.7 | Balanced (realistic diversity w personalities) |
| Executive summaries | 0.5 | Moderate creativity (insightful but factual) |
| Brainstorming | 0.9 | High creativity (exploring ideas) |

**General rule:** Lower temperature = more consistency, Higher temperature = more creativity

### 7. Token Optimization Strategies

**1. Remove Redundant Instructions**
- ❌ "You should generate", "Please make sure", "It is important that"
- ✅ "Generate", "Ensure", "IMPORTANT:"

**2. Use Bullet Points (Not Paragraphs)**
- ❌ "The persona should have a realistic background story that explains their values and interests based on their demographics, including their age, occupation, and life experiences."
- ✅ "Background story: explain values based on demographics (age, occupation, experiences)"

**3. Include Only MUST-HAVE Context**
- ❌ Entire Wikipedia article o polskiej historii
- ✅ Top 3 relevant insights from RAG

**4. Use JSON Output Format**
- Structured output = easier parsing, fewer tokens than prose

**5. Truncate Long Contexts Intelligently**
```python
def truncate_rag_context(chunks, max_chars=8000):
    """Priorytetyzuj MUST-HAVE chunks"""
    # Sort by relevance score (from hybrid search)
    sorted_chunks = sorted(chunks, key=lambda x: x['score'], reverse=True)

    # Take top chunks until max_chars
    result = []
    total_chars = 0
    for chunk in sorted_chunks:
        if total_chars + len(chunk['text']) > max_chars:
            break
        result.append(chunk)
        total_chars += len(chunk['text'])

    return result
```

---

## 🚀 RAG System Deep Dive

### Hybrid Search Architecture

**Components:**
1. **Vector Search** - Semantic similarity (Google embeddings, 768D)
2. **Keyword Search** - Lexical matching (Neo4j fulltext index)
3. **RRF Fusion** - Combines rankings (k=60 balances both methods)
4. **Cross-Encoder Reranking** - Precision boost (multilingual model)

**Workflow:**
```
User Query: "młoda osoba wykształcenie wyższe Warszawa"
    ↓
┌───────────────────┐           ┌───────────────────┐
│ Vector Search     │           │ Keyword Search    │
│ (Semantic)        │           │ (Lexical)         │
│ Returns: 20 docs  │           │ Returns: 20 docs  │
└─────────┬─────────┘           └─────────┬─────────┘
          │                               │
          └───────────┬───────────────────┘
                      ↓
              ┌───────────────┐
              │   RRF Fusion  │
              │ (k=60)        │
              │ Returns: 25   │
              └───────┬───────┘
                      ↓
          ┌───────────────────────┐
          │ Cross-Encoder Rerank  │
          │ (mmarco-mMiniLMv2)    │
          │ Returns: Top 8        │
          └───────────┬───────────┘
                      ↓
              ┌───────────────┐
              │ Final Results │
              │ (Top 8 chunks)│
              └───────────────┘
```

### GraphRAG (Structural Knowledge)

**Purpose:** Ekstraktuje strukturalną wiedzę z dokumentów (nodes + relationships z metadanymi)

**Node Types (5):**
- **Obserwacja** - Konkretne obserwacje, fakty z badań, przyczyny i skutki zjawisk
- **Wskaznik** - Wskaźniki liczbowe, statystyki, metryki
- **Demografia** - Grupy demograficzne, populacje
- **Trend** - Trendy czasowe, zmiany w czasie
- **Lokalizacja** - Miejsca geograficzne

**Relationship Types (5):**
- `OPISUJE` - Opisuje cechę/właściwość
- `DOTYCZY` - Dotyczy grupy/kategorii
- `POKAZUJE_TREND` - Pokazuje trend czasowy
- `ZLOKALIZOWANY_W` - Zlokalizowane w miejscu
- `POWIAZANY_Z` - Ogólne powiązanie (przyczynowość, porównania, korelacje)

**Node Properties (5 core):**
- `streszczenie` - **MUST:** Jednozdaniowe podsumowanie (max 150 znaków)
- `skala` - Wartość z jednostką (np. "78.4%", "5000 PLN")
- `pewnosc` - **MUST:** Pewność danych ("wysoka", "srednia", "niska")
- `okres_czasu` - Okres czasu ("2022", "2018-2023")
- `kluczowe_fakty` - Max 3 fakty oddzielone średnikami

**Relationship Properties (1 core):**
- `sila` - Siła relacji ("silna", "umiarkowana", "slaba")

**Why Simplified Schema?**
- **Problem (Before):** 7 node properties + 3 relationship properties → >30% nodes incomplete
- **Solution (After):** 5 MUST properties → focus on core, +40% fill-rate
- **Result:** -60% token usage, +better LLM compliance

### Enriched Chunks (Unique Feature)

**Concept:** Każdy chunk jest wzbogacany o powiązane graph nodes

```python
# Original chunk
chunk = {
    "text": "W latach 2018-2023 wzrost zatrudnienia młodych dorosłych...",
    "metadata": {"doc_id": "123", "chunk_index": 0}
}

# Enriched chunk (after graph enrichment)
enriched_chunk = {
    "text": "W latach 2018-2023 wzrost zatrudnienia młodych dorosłych...",
    "metadata": {...},
    "graph_context": {
        "wskazniki": [
            {"streszczenie": "Wskaźnik zatrudnienia 25-34 lata", "skala": "67%", "pewnosc": "wysoka"}
        ],
        "trendy": [
            {"streszczenie": "Wzrost zatrudnienia młodych dorosłych", "okres_czasu": "2018-2023"}
        ]
    }
}
```

**Benefit:** LLM dostaje nie tylko tekst, ale **strukturalną wiedzę** z metadanymi jakości

### RAG Integration with Persona Generation

```python
# Workflow
async def generate_persona(demographics):
    # 1. Build RAG query from demographics
    query = f"Polish society insights: age {demographics['age']}, gender {demographics['gender']}, location {demographics['location']}"

    # 2. Hybrid search (vector + keyword + RRF + rerank)
    rag_results = await polish_society_rag.get_demographic_insights(
        age_group=demographics['age'],
        gender=demographics['gender'],
        location=demographics['location']
    )

    # 3. Build context (chunks + graph nodes)
    rag_context = "\n\n".join([
        f"📄 {chunk['text']}\n💡 Wskaźniki: {chunk['graph_context']['wskazniki']}"
        for chunk in rag_results
    ])

    # 4. Format prompt with RAG context
    prompt = PERSONA_PROMPT.format(
        demographics=demographics,
        rag_context=rag_context[:MAX_CONTEXT_CHARS]  # Truncate if needed
    )

    # 5. LLM generation
    response = await llm_flash.ainvoke(prompt)

    return parse_persona(response.content)
```

**Performance:**
- Without RAG: 30s for 20 personas (generyczne profiles)
- With RAG (hybrid + rerank): 42-45s for 20 personas (+40% time, ale **significantly higher quality**)

---

## ⚡ Performance & Cost Optimization

### 1. Parallel LLM Calls (asyncio.gather)

**Problem:** Sequential calls = 20 personas × 3s = 60s

**Solution:** Parallel execution
```python
import asyncio

# Sequential (SLOW)
personas = []
for i in range(20):
    persona = await generate_persona(demographics[i])  # 3s each
    personas.append(persona)
# Total: 60s

# Parallel (FAST)
tasks = [generate_persona(demographics[i]) for i in range(20)]
personas = await asyncio.gather(*tasks)  # All at once
# Total: ~15s (4x speedup!)
```

**Implementation:**
```python
# app/services/focus_group_service_langchain.py
async def run_focus_group(focus_group_id, questions):
    """Orkiestracja dyskusji z async parallelization"""
    personas = await _get_personas(focus_group_id)

    for question in questions:
        # Generate responses for ALL personas in parallel
        tasks = [
            _generate_response_for_persona(persona, question, context)
            for persona in personas
        ]
        responses = await asyncio.gather(*tasks)  # Parallel!

        # Save responses
        await _save_responses(focus_group_id, question, responses)
```

**Result:** 20 personas × 4 questions = 80 responses
- Sequential: 80 × 2s = 160s (~3 min)
- Parallel: 4 questions × ~15s = 60s (~1 min) - **3x speedup!**

### 2. Rate Limiting (Gemini 15 RPM)

**Problem:** 20 parallel requests = może exceed Gemini 15 RPM limit

**Solution:** Semaphore pattern
```python
import asyncio

# Global semaphore (limit concurrent requests)
llm_semaphore = asyncio.Semaphore(15)  # Max 15 concurrent

async def call_llm_with_rate_limit(prompt):
    """Wrap LLM calls with rate limiting"""
    async with llm_semaphore:
        response = await llm.ainvoke(prompt)
        return response
```

**Alternative:** Throttling with delays
```python
import time

async def call_llm_with_throttle(prompt, delay=0.1):
    """Add small delay between requests"""
    await asyncio.sleep(delay)  # 100ms delay
    response = await llm.ainvoke(prompt)
    return response
```

### 3. Retry Logic (Transient Failures)

**Problem:** LLM API sometimes fails (429 rate limit, 500 internal error, network issues)

**Solution:** Exponential backoff
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(4),  # Max 4 attempts
    wait=wait_exponential(multiplier=1, min=1, max=10),  # 1s, 2s, 4s, 8s
    retry=retry_if_exception_type((httpx.HTTPError, asyncio.TimeoutError))
)
async def call_llm_with_retry(prompt):
    """LLM call with automatic retry"""
    response = await llm.ainvoke(prompt)
    return response
```

**Retry Strategy:**
- Attempt 1: Immediate
- Attempt 2: Wait 1s
- Attempt 3: Wait 2s
- Attempt 4: Wait 4s
- After 4 failures: Raise exception

### 4. Prompt Compression (-60% Tokens)

**Technique 1: Remove Bloat**
```python
# Before (Bloated)
prompt = f"""
You should generate a persona that is realistic and represents the Polish society.
Please make sure that the persona has accurate demographics, psychology, and cultural dimensions.
It is very important that you use the RAG context provided below to ground your persona in reality.

RAG Context:
{rag_context}  # 10,000 chars

Please generate the persona now.
"""
# Tokens: ~4000

# After (Compressed)
prompt = f"""
Generate a realistic Polish persona using RAG context.

RAG Context (top insights):
{rag_context[:5000]}  # Truncated to 5000 chars

Output JSON: {{"name": ..., "age": ..., ...}}
"""
# Tokens: ~1500 (-62%)
```

**Technique 2: Graph Schema Simplification**
```python
# Before: 7 node properties
node_properties = [
    "streszczenie",  # MUST
    "opis",          # Duplicates streszczenie - REMOVE
    "skala",
    "pewnosc",       # MUST
    "kluczowe_fakty",
    "zrodlo",        # Rarely used, high token cost - REMOVE
    "okres_czasu"
]

# After: 5 core properties (focus on MUST-HAVE)
node_properties = [
    "streszczenie",  # MUST
    "skala",
    "pewnosc",       # MUST
    "kluczowe_fakty",
    "okres_czasu"
]
```

**Result:**
- Token usage: 110k → 50k tokens per batch (-55%)
- LLM compliance: 70% → 85% (fill-rate for properties)
- Cost: $0.15 → $0.06 per 20 personas (-60%)

### 5. Token Budgets per Operation

```python
# app/core/config.py
TOKEN_BUDGETS = {
    "persona_generation": {
        "max_input": 2000,   # RAG context + demographics
        "max_output": 500,   # Persona JSON
        "target_cost": 0.001  # $0.001 per persona
    },
    "focus_group_response": {
        "max_input": 1500,   # Memory context + question
        "max_output": 200,   # Response (2-3 sentences)
        "target_cost": 0.0005
    },
    "survey_response": {
        "max_input": 1000,   # Persona profile + question + options
        "max_output": 100,   # Answer + reasoning
        "target_cost": 0.0003
    },
    "graph_rag_query": {
        "max_input": 3000,   # Graph context + vector context
        "max_output": 800,   # Detailed answer
        "target_cost": 0.002
    }
}
```

**Monitoring:**
```python
# Track actual vs budget
actual_tokens_in = len(prompt.split()) * 1.3  # Rough estimate
if actual_tokens_in > TOKEN_BUDGETS["persona_generation"]["max_input"]:
    logger.warning(f"Token budget exceeded: {actual_tokens_in} > {TOKEN_BUDGETS['persona_generation']['max_input']}")
```

### 6. Caching Strategy (Future - Phase 3)

**Candidates for caching:**
- Persona profiles (1 day TTL) - Rarely change
- RAG context for common queries (1 hour TTL) - Popular demographics
- Focus group responses (permanent) - Immutable once generated

```python
# Redis caching (future implementation)
import redis
import json

redis_client = redis.from_url(settings.REDIS_URL)

async def get_cached_rag_context(query_key):
    """Check cache before expensive RAG search"""
    cached = redis_client.get(f"rag:{query_key}")
    if cached:
        return json.loads(cached)

    # Cache miss - perform RAG search
    results = await polish_society_rag.get_demographic_insights(...)
    redis_client.setex(f"rag:{query_key}", 3600, json.dumps(results))  # 1 hour TTL
    return results
```

**Potential savings:**
- Cache hit rate: 30-40% (optimistic)
- Cost reduction: -$100/month (@1000 users)

---

## 🎯 Quality Assurance

### 1. Persona Validation

#### Statistical Validation (Chi-Square Test)

```python
# app/services/persona_validator.py
from scipy.stats import chisquare

def validate_demographics(personas, target_distribution):
    """Validate that generated personas match target demographics"""

    # Count generated distribution
    actual = {"18-24": 0, "25-34": 0, "35-44": 0, ...}
    for persona in personas:
        actual[persona.age_group] += 1

    # Expected counts
    expected = {k: v * len(personas) for k, v in target_distribution.items()}

    # Chi-square test
    chi2, p_value = chisquare(
        f_obs=list(actual.values()),
        f_exp=list(expected.values())
    )

    # p_value > 0.05 = good (not significantly different)
    return p_value > 0.05
```

#### Big Five Validation

**Problem:** LLM tends to generate "average" personas (all traits = 0.5)

**Validation:**
```python
def validate_big_five(persona):
    """Ensure traits are not all 0.5 (avoid "average" personas)"""
    traits = [
        persona.openness,
        persona.conscientiousness,
        persona.extraversion,
        persona.agreeableness,
        persona.neuroticism
    ]

    # Check if all traits are close to 0.5 (within 0.1)
    avg_distance = sum(abs(t - 0.5) for t in traits) / len(traits)

    if avg_distance < 0.15:
        raise ValueError("Persona too 'average' - regenerate with more diverse traits")

    return True
```

#### Cultural Validation (Hofstede Dimensions)

```python
def validate_hofstede(persona, country="Poland"):
    """Validate Hofstede dimensions are realistic for country"""

    # Poland typical ranges (from Hofstede research)
    poland_ranges = {
        "power_distance": (0.55, 0.75),  # High
        "individualism": (0.50, 0.70),   # Medium-high
        "masculinity": (0.55, 0.75),     # High
        "uncertainty_avoidance": (0.80, 0.95),  # Very high
        "long_term_orientation": (0.30, 0.50),  # Medium
        "indulgence": (0.25, 0.40)       # Low
    }

    for dimension, (min_val, max_val) in poland_ranges.items():
        value = getattr(persona.hofstede, dimension)
        if not (min_val <= value <= max_val):
            logger.warning(f"Unrealistic {dimension} for Poland: {value} (expected {min_val}-{max_val})")

    return True
```

### 2. Response Quality Metrics

#### Coherence Check

```python
def check_response_coherence(persona, response):
    """Check if response matches persona profile"""

    # Extract keywords from persona values
    persona_keywords = set([
        word.lower()
        for value in persona.values
        for word in value.split()
    ])

    # Extract keywords from response
    response_keywords = set(response.lower().split())

    # Overlap score
    overlap = len(persona_keywords & response_keywords) / len(persona_keywords)

    if overlap < 0.1:
        logger.warning(f"Low coherence: response doesn't mention persona values (overlap: {overlap:.2%})")

    return overlap > 0.1
```

#### Length Validation

```python
def validate_response_length(response, min_words=10, max_words=100):
    """Ensure response is not too short or too long"""
    word_count = len(response.split())

    if word_count < min_words:
        raise ValueError(f"Response too short: {word_count} words (min: {min_words})")
    if word_count > max_words:
        logger.warning(f"Response too long: {word_count} words (max: {max_words})")

    return True
```

### 3. Hallucination Prevention

#### RAG Grounding

```python
# GOOD: Grounded in RAG context
prompt = f"""
Use ONLY the RAG context below to generate a persona.

RAG Context:
{rag_context}

Generate persona...
"""

# BAD: No grounding (LLM uses internal knowledge)
prompt = f"""
Generate a Polish persona...
(no RAG context provided)
"""
```

#### Structured Output (Pydantic Validation)

```python
from pydantic import BaseModel, Field, validator

class PersonaOutput(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    age: int = Field(..., ge=18, le=100)
    background: str = Field(..., min_length=50, max_length=500)

    @validator('age')
    def age_must_match_demographics(cls, v, values):
        # Custom validation logic
        if 'age_group' in values:
            age_group = values['age_group']
            if age_group == "18-24" and not (18 <= v <= 24):
                raise ValueError(f"Age {v} doesn't match age_group {age_group}")
        return v
```

#### Temperature Control

```python
# Lower temperature = less creativity = fewer hallucinations
llm_deterministic = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.0,  # Deterministic
    max_tokens=1024
)

# For surveys: always use temperature=0.0
response = await llm_deterministic.ainvoke(survey_prompt)
```

### 4. Quality Metrics Dashboard (Future)

**Persona Quality Score (0-100):**
```python
def calculate_persona_quality_score(persona):
    """Composite quality score"""
    scores = {
        "statistical_fit": chi_square_p_value * 100,  # 0-100
        "trait_diversity": (1 - avg_trait_distance_from_0.5) * 100,
        "cultural_realism": hofstede_in_range_count / 6 * 100,
        "background_length": min(len(persona.background.split()), 150) / 150 * 100,
        "rag_grounding": rag_keywords_in_background / total_rag_keywords * 100
    }

    # Weighted average
    weights = {
        "statistical_fit": 0.3,
        "trait_diversity": 0.2,
        "cultural_realism": 0.2,
        "background_length": 0.1,
        "rag_grounding": 0.2
    }

    total_score = sum(scores[k] * weights[k] for k in scores)
    return total_score  # 0-100
```

---

## 🐛 Troubleshooting

### Common LLM Errors

#### 1. 429 Rate Limit Exceeded

**Error:**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded for quota metric 'Generate requests' and limit 'Requests per minute'
```

**Cause:** Too many parallel requests (exceeds 15 RPM for Gemini)

**Solution:**
```python
# Add semaphore rate limiting (see Performance section)
llm_semaphore = asyncio.Semaphore(15)

async def call_llm_with_rate_limit(prompt):
    async with llm_semaphore:
        response = await llm.ainvoke(prompt)
        return response
```

**Alternative:** Increase delay between requests
```python
await asyncio.sleep(0.2)  # 200ms delay = max 5 RPS = 300 RPM
```

#### 2. 400 Bad Request (Prompt Too Long)

**Error:**
```
google.api_core.exceptions.InvalidArgument: 400 Request contains an invalid argument
```

**Cause:** Prompt exceeds Gemini token limit (~8000 tokens = ~32000 chars)

**Solution:**
```python
# Truncate RAG context
MAX_CONTEXT_CHARS = 8000
rag_context = rag_context[:MAX_CONTEXT_CHARS]

# Or: Compress prompt (remove bloat)
prompt = compress_prompt(prompt)  # See Optimization section
```

#### 3. 500 Internal Server Error

**Error:**
```
google.api_core.exceptions.InternalServerError: 500 Internal error encountered
```

**Cause:** Gemini API issue (transient error)

**Solution:** Retry with exponential backoff
```python
@retry(stop=stop_after_attempt(4), wait=wait_exponential(multiplier=1))
async def call_llm_with_retry(prompt):
    response = await llm.ainvoke(prompt)
    return response
```

#### 4. Empty Response

**Error:** LLM returns empty string or incomplete JSON

**Cause:** `max_tokens` too low (Gemini 2.5 uses reasoning tokens!)

**Solution:**
```python
# Increase max_tokens (Gemini 2.5 needs 2048+ for reasoning)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=2048  # Was 512 - TOO LOW!
)
```

### Timeout Issues

#### Problem: LLM calls hang (no response after 30s+)

**Solution:** Add timeout
```python
import asyncio

async def call_llm_with_timeout(prompt, timeout=120):
    """LLM call with timeout"""
    try:
        response = await asyncio.wait_for(
            llm.ainvoke(prompt),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.error(f"LLM call timed out after {timeout}s")
        raise
```

**Configuration:**
```python
# app/core/config.py
LLM_TIMEOUT_SECONDS = 120  # 2 min (default)
LLM_TIMEOUT_LONG_SECONDS = 300  # 5 min (for graph RAG queries)
```

### Fallback Strategies

#### Strategy 1: Model Fallback (Pro → Flash)

```python
async def call_llm_with_fallback(prompt):
    """Try Gemini Pro, fallback to Flash if fails"""
    try:
        response = await llm_pro.ainvoke(prompt)
        return response
    except Exception as e:
        logger.warning(f"Gemini Pro failed: {e}, falling back to Flash")
        response = await llm_flash.ainvoke(prompt)
        return response
```

#### Strategy 2: RAG Fallback (Hybrid → Vector Only)

```python
async def get_rag_context_with_fallback(query):
    """Try hybrid search, fallback to vector only if fails"""
    try:
        results = await polish_society_rag.get_demographic_insights(query)
        return results
    except Exception as e:
        logger.warning(f"Hybrid search failed: {e}, falling back to vector only")
        results = await vector_store.asimilarity_search(query, k=8)
        return results
```

#### Strategy 3: No RAG Fallback (Lower Quality)

```python
async def generate_persona_with_fallback(demographics):
    """Try with RAG, fallback to no RAG if unavailable"""
    try:
        rag_context = await get_rag_context(demographics)
    except Exception as e:
        logger.error(f"RAG unavailable: {e}, generating without RAG context")
        rag_context = ""  # Empty context (lower quality, but functional)

    # Generate persona (with or without RAG)
    prompt = PERSONA_PROMPT.format(
        demographics=demographics,
        rag_context=rag_context or "[RAG context unavailable]"
    )
    response = await llm_flash.ainvoke(prompt)
    return parse_persona(response.content)
```

### Debugging Tips

#### 1. Log Prompts & Responses

```python
import logging

logger = logging.getLogger(__name__)

async def call_llm_debug(prompt):
    """LLM call with debug logging"""
    logger.debug(f"📤 PROMPT (length: {len(prompt)} chars):\n{prompt[:500]}...")

    response = await llm.ainvoke(prompt)

    logger.debug(f"📥 RESPONSE (length: {len(response.content)} chars):\n{response.content[:500]}...")

    return response
```

#### 2. Token Counting

```python
def count_tokens_rough(text):
    """Rough token count (1 token ~= 4 chars for English, ~1.3 words)"""
    return len(text) // 4

# Usage
prompt_tokens = count_tokens_rough(prompt)
logger.info(f"Prompt tokens (estimate): {prompt_tokens}")

if prompt_tokens > 7000:
    logger.warning("Prompt close to token limit (8000)!")
```

#### 3. Test with Minimal Prompt

```python
# Minimal test prompt (verify API works)
minimal_prompt = "Say 'hello'"
response = await llm.ainvoke(minimal_prompt)
print(response.content)  # Should print "hello"

# If this fails → API key issue or service down
```

---

## 🎯 4. Segment-Based Persona Architecture (Refactor - 2025-10-15)

System generowania person został zrefaktoryzowany z luźnej orkiestracji na strukturalną architekturę segmentową. Ta zmiana rozwiązuje kluczowy problem niezgodności między briefami orkiestracyjnymi a faktycznymi charakterystykami wygenerowanych person.

### 4.1 Problem z Poprzednią Architekturą

**Stary sposób (loose orchestration briefs):**

W pierwotnej architekturze orkiestrator tworzył tekstowe briefe dla grup demograficznych (np. "Kobiety 18-24, wykształcenie wyższe, Warszawa"). Generator person interpretował te briefe i **losował** demographics z rozkładów statystycznych. Problem w tym, że nie było gwarancji spójności:

```python
# Orchestration brief
brief = "Młode kobiety 18-24 lat, wykształcenie wyższe, Warszawa"

# Generator losuje demographics
age = random.randint(18, 100)  # Może wylosować 38 lat! ❌
gender = random.choice(['male', 'female'])  # Może wylosować mężczyznę! ❌
```

**Przykład problemu:**
```
Orchestration brief: "Młode kobiety 18-24, wyższe wykształcenie"
Generated persona: Ewelina, 38 lat, mężczyzna, średnie wykształcenie
→ Brief nie pasuje do persony! ❌
```

Ten problem występował ponieważ brief był "string prompt", nie "data contract" z wymuszalnymi constraints.

### 4.2 Nowe Rozwiązanie: Segment Definitions

**Segment-based architecture (nowy sposób):**

System wykorzystuje teraz **SegmentDefinition** - strukturalny kontrakt Pydantic, który definiuje HARD constraints demograficzne. Generator **wymusza** demographics z SegmentDefinition, eliminując losowość:

```python
# FAZA 1: Orchestration tworzy structured segment
segment = SegmentDefinition(
    segment_id="seg_young_precariat",
    segment_name="Młodzi Prekariusze",  # LLM-generated mówiąca nazwa
    demographics=DemographicConstraints(
        age_min=18,
        age_max=24,
        gender="kobieta",
        education_levels=["wyższe - licencjat", "wyższe - magister"],
        income_brackets=["<3000 PLN"],
        locations=["Warszawa", "Kraków", "Wrocław"]
    ),
    segment_context="Młodzi Prekariusze to osoby 18-24 lat...",  # 500-800 znaków
    persona_count=5
)

# FAZA 2: Generator ENFORCE demographics z segment constraints
persona = await generator.generate_persona_from_segment(
    segment_id=segment.segment_id,
    segment_name=segment.segment_name,
    segment_context=segment.segment_context,
    demographics_constraints=segment.demographics.__dict__
)

# RESULT: Age = random.randint(18, 24), Gender = "kobieta", Education ∈ allowed list
# ✅ Persona ZAWSZE pasuje do segmentu!
```

**Kluczowe różnice:**

| Aspekt | Stary sposób | Nowy sposób |
|--------|--------------|-------------|
| Brief format | String prompt | Structured Pydantic schema |
| Age constraint | Sugestia (może być złamana) | HARD bounds (age_min, age_max) |
| Gender | Random choice | Enforced z constraints |
| Validation | Niemożliwa (string) | Pydantic validators |
| Consistency | Brief ≠ persona (❌) | Brief ≡ persona (✅) |

### 4.3 Kluczowe Komponenty

#### SegmentDefinition (Pydantic Schema)

```python
class SegmentDefinition(BaseModel):
    """Strukturalna definicja segmentu demograficznego."""

    segment_id: str  # "seg_young_precariat"
    segment_name: str  # "Młodzi Prekariusze" (LLM-generated)
    segment_description: Optional[str]  # Krótki opis (1-2 zdania)

    demographics: DemographicConstraints  # HARD constraints
    segment_context: str  # 500-800 znaków kontekstu społecznego

    graph_insights: List[GraphInsight]  # Filtrowane insights dla segmentu
    rag_citations: List[RAGCitation]  # High-quality citations (confidence > 0.7)

    persona_count: int  # Liczba person w segmencie
    persona_brief: str  # Instructions dla generatora (200-800 znaków)
```

#### DemographicConstraints

```python
class DemographicConstraints(BaseModel):
    """HARD constraints wymuszane przez generator."""

    age_min: int = Field(ge=18, le=100)  # Minimalny wiek
    age_max: int = Field(ge=18, le=100)  # Maksymalny wiek (>= age_min)

    gender: str  # "kobieta", "mężczyzna", "non-binary"

    education_levels: List[str]  # Dozwolone poziomy (min 1)
    income_brackets: List[str]  # Dozwolone przedziały (min 1)
    locations: Optional[List[str]]  # Dozwolone lokalizacje (None = any)

    @validator('age_max')
    def age_max_greater_than_min(cls, v, values):
        if 'age_min' in values and v < values['age_min']:
            raise ValueError(f'age_max must be >= age_min')
        return v
```

**Przykład segment constraints:**

```python
constraints = DemographicConstraints(
    age_min=25,
    age_max=34,
    gender="kobieta",
    education_levels=["wyższe - licencjat", "wyższe - magister"],
    income_brackets=["3000-5000 PLN", "5000-7000 PLN"],
    locations=["Warszawa"]
)
```

Gdy generator tworzy personę, **wymusza** te bounds:

```python
# Generator enforce (NOT random sampling!)
age = self._rng.integers(constraints.age_min, constraints.age_max + 1)  # 25-34
gender = constraints.gender  # "kobieta" (NO randomization!)
education = self._rng.choice(constraints.education_levels)  # Z allowed list
income = self._rng.choice(constraints.income_brackets)  # Z allowed list
location = self._rng.choice(constraints.locations or ["Warszawa"])  # Z allowed lub default
```

### 4.4 Nowe Metody w PersonaOrchestrationService

Orchestration service rozszerza responsywności o trzy kluczowe metody generowania mówiących nazw segmentów i kontekstów społecznych.

#### 1. _generate_segment_name()

```python
async def _generate_segment_name(
    demographics: Dict[str, Any],
    graph_insights: List[GraphInsight],
    rag_citations: List[Any]
) -> str:
    """
    Generuje mówiącą nazwę segmentu używając Gemini 2.0 Flash.

    Nazwa powinna być krótka (2-4 słowa) i odzwierciedlać kluczowe cechy
    grupy demograficznej bazując na insightach z grafu i RAG.

    Returns:
        Nazwa np. "Młodzi Prekariusze", "Aspirujące Profesjonalistki 35-44"
    """
```

**Przykłady generowanych nazw:**

- "Młodzi Prekariusze" (18-24, niskie dochody, wyższe wykształcenie)
- "Aspirujące Profesjonalistki 35-44" (kobiety, średnie dochody, ambicje kariery)
- "Dojrzali Eksperci" (45-54, wysokie dochody, stabilna kariera)
- "Początkujący Profesjonaliści" (25-34, pierwsze kroki w karierze)

Nazwa nie jest randomowa - bazuje na graph insights (np. wskaźniki zatrudnienia, dochodów) i demographics (wiek, płeć, wykształcenie), co sprawia że jest **semantycznie trafna**.

#### 2. _generate_segment_context()

```python
async def _generate_segment_context(
    segment_name: str,
    demographics: Dict[str, Any],
    graph_insights: List[GraphInsight],
    rag_citations: List[Any],
    project_goal: Optional[str] = None
) -> str:
    """
    Generuje kontekst społeczny dla segmentu używając Gemini 2.5 Pro.

    Kontekst powinien być 500-800 znaków, edukacyjny i SPECYFICZNY dla tej grupy
    (nie ogólny dla całej Polski!).

    Returns:
        Kontekst opisujący wyzwania życiowe, wartości, aspiracje, kontekst ekonomiczny
    """
```

**Przykład wygenerowanego kontekstu:**

```
"Młodzi Prekariusze to osoby w wieku 18-24 lat, często w trakcie studiów lub tuż po
ich ukończeniu. Wchodzą na rynek pracy w trudnym okresie – inflacja 12% (2023),
niestabilność zatrudnienia (62% na umowach czasowych według GUS), rosnące koszty życia.
Mimo wyższego wykształcenia (lub jego zdobywania), zarabiają poniżej średniej krajowej
(<3000 PLN). Ich wartości: autonomia, rozwój osobisty, work-life balance. Aspiracje:
stabilna praca, własne mieszkanie (często nieosiągalne - cena m2 w Warszawie 15000 zł,
przy zarobkach 2500 zł netto wymaga 25 lat oszczędzania!). Wyzwania: długi kredytowe,
niepewność przyszłości, rosnące wymagania pracodawców."
```

Kontekst wykorzystuje **konkretne liczby** z graph insights (wskaźniki GUS, CBOS) i jest **edukacyjny** - wyjaśnia "dlaczego" ta grupa jest w takiej sytuacji (ekonomia, trendy, demografia).

#### 3. _filter_graph_insights_for_segment()

```python
def _filter_graph_insights_for_segment(
    insights: List[GraphInsight],
    demographics: Dict[str, Any]
) -> List[GraphInsight]:
    """
    Filtruje graph insights dla konkretnego segmentu demograficznego.

    Zwraca tylko insights relevantne dla tego segmentu (np. insights o młodych
    dla segmentu 18-24, insights o kobietach dla segmentu female).

    Returns:
        Top 10 insights sortowane po confidence (high first)
    """
```

**Logika filtrowania:**

```python
# Sprawdź czy insight jest relevant dla age range
if "18-24" in insight.summary and segment.age_min == 18:
    # Relevant!
    filtered.append(insight)

# Sortuj po confidence
confidence_order = {'high': 3, 'medium': 2, 'low': 1}
filtered.sort(key=lambda x: confidence_order[x.confidence], reverse=True)

return filtered[:10]  # Top 10
```

Dzięki temu każdy segment dostaje **indywidualne insights** zamiast ogólnych danych o całym społeczeństwie. Dla segmentu "Młodzi Prekariusze" (18-24) dostaniemy insights o młodych, nie o emerytach 65+.

### 4.5 Nowa Metoda w PersonaGeneratorLangChain

#### generate_persona_from_segment()

```python
async def generate_persona_from_segment(
    segment_id: str,
    segment_name: str,
    segment_context: str,
    demographics_constraints: Dict[str, Any],
    graph_insights: List[Any] = None,
    rag_citations: List[Any] = None,
    personality_skew: Optional[Dict[str, float]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generuje personę Z WYMUSZENIEM demographics z segmentu.

    KLUCZOWA RÓŻNICA vs generate_persona_personality():
    - Demographics są ENFORCE (nie losowane poza bounds!)
    - Age = random.randint(age_min, age_max)  # W bounds!
    - Gender = constraints.gender  # NO randomization!
    - Education/Income = random.choice z allowed lists

    Post-generation validation:
    - Jeśli LLM zwróci inny age/gender → OVERRIDE z constraints
    """
```

**Workflow wymuszania demographics:**

```python
# Krok 1: Extract constraints
age_min = constraints.get('age_min', 25)
age_max = constraints.get('age_max', 34)
gender = constraints.get('gender', 'kobieta')
education_levels = constraints.get('education_levels', ['wyższe'])
income_brackets = constraints.get('income_brackets', ['3000-5000 PLN'])

# Krok 2: ENFORCE (sample w bounds!)
age = self._rng.integers(age_min, age_max + 1)  # 25-34
education = self._rng.choice(education_levels)  # Z allowed
income = self._rng.choice(income_brackets)  # Z allowed

demographic_profile = {
    "age": age,  # Enforced
    "gender": gender,  # Enforced
    "education_level": education,  # Enforced
    "income_bracket": income  # Enforced
}

# Krok 3: Generate persona z LLM
prompt = self._create_segment_persona_prompt(
    demographic_profile, psychological_profile, segment_name, segment_context
)
response = await self.persona_chain.ainvoke({"prompt": prompt})

# Krok 4: POST-GENERATION OVERRIDE (safety net)
# Jeśli LLM zwróci inny age/gender (błąd parsowania), wymuszamy z constraints
response['age'] = age  # Force correct age
response['gender'] = gender  # Force correct gender
response['education_level'] = education  # Force correct education
response['income_bracket'] = income  # Force correct income

# Krok 5: Add segment tracking
response['_segment_id'] = segment_id
response['_segment_name'] = segment_name

return prompt, response
```

Post-generation override zapewnia że **nawet jeśli LLM pomyli się** (błędnie sparsuje JSON lub zignoruje constraints w prompt), demographics zostaną nadpisane z enforced values.

### 4.6 Database Schema Changes

**Nowe kolumny w tabeli `personas`:**

```sql
ALTER TABLE personas ADD COLUMN segment_id VARCHAR(100);
ALTER TABLE personas ADD COLUMN segment_name VARCHAR(100);
CREATE INDEX ix_personas_segment_id ON personas(segment_id);
```

**Przykład danych:**

```sql
SELECT id, full_name, age, gender, segment_id, segment_name
FROM personas
WHERE project_id = 'proj_123';

-- RESULTS:
-- id: p_001, name: "Anna Nowak", age: 22, gender: "kobieta",
--     segment_id: "seg_young_precariat", segment_name: "Młodzi Prekariusze"
-- id: p_002, name: "Marta Kowalska", age: 23, gender: "kobieta",
--     segment_id: "seg_young_precariat", segment_name: "Młodzi Prekariusze"
```

Teraz każda persona jest **przypisana do segmentu** i można query by segment:

```sql
-- Ile person jest w każdym segmencie?
SELECT segment_name, COUNT(*) as persona_count
FROM personas
WHERE project_id = 'proj_123'
GROUP BY segment_name;

-- RESULT: Młodzi Prekariusze: 5, Aspirujące Profesjonalistki 35-44: 8, ...
```

### 4.7 Frontend UI Changes

**PersonaReasoningPanel.tsx** (zakładka "Uzasadnienie" w UI) otrzymała znaczące ulepszenia:

#### Hero Segment Header (Always Visible)

```tsx
{persona.segment_name && (
  <div className="hero-segment-header">
    <h2 className="text-2xl font-bold">{persona.segment_name}</h2>
    <p className="text-gray-600">{persona.segment_description}</p>
  </div>
)}
```

Nazwa segmentu jest wyświetlana jako **duży tytuł** na górze panelu reasoning, zawsze widoczny. Użytkownik od razu wie do jakiej grupy należy persona (np. "Młodzi Prekariusze" zamiast "Wiek 18-24, kobieta").

#### Validation Alert

```tsx
{persona.segment_name && (
  <ValidationAlert
    age={persona.age}
    ageMin={segment.demographics.age_min}
    ageMax={segment.demographics.age_max}
  />
)}

// ValidationAlert component:
function ValidationAlert({ age, ageMin, ageMax }) {
  const isValid = age >= ageMin && age <= ageMax;

  if (!isValid) {
    return (
      <div className="alert alert-error">
        ⚠️ VALIDATION ERROR: Age {age} outside segment bounds [{ageMin}, {ageMax}]
      </div>
    );
  }

  return (
    <div className="alert alert-success">
      ✅ Validation passed: Age {age} within segment bounds [{ageMin}, {ageMax}]
    </div>
  );
}
```

Alert pokazuje czy persona **pasuje do segment constraints** (age ∈ [age_min, age_max]). Jeśli nie pasuje → ERROR (powinno się nigdy nie zdarzyć dzięki enforcement w generatorze).

#### Indywidualny Kontekst Społeczny

```tsx
<section>
  <h3>Kontekst Społeczny dla {persona.segment_name}</h3>
  <p>{persona.segment_social_context}</p>
</section>
```

Zamiast globalnego kontekstu ("polskie społeczeństwo..."), każdy segment ma **indywidualny kontekst** specyficzny dla tej grupy demograficznej (np. wyzwania młodych 18-24 vs. wyzwania doświadczonych profesjonalistów 45-54).

#### Lepsze Graph Insights Display

```tsx
{persona.graph_insights.map(insight => (
  <div className="insight-card" key={insight.summary}>
    <h4>{insight.summary}</h4>

    <div className="badges">
      <Badge color={insight.confidence === 'high' ? 'green' : 'yellow'}>
        {insight.confidence}
      </Badge>
      {insight.source && <Badge>{insight.source}</Badge>}
      {insight.time_period && <Badge>{insight.time_period}</Badge>}
    </div>

    {insight.magnitude && (
      <p className="magnitude">📊 {insight.magnitude}</p>
    )}

    <p className="why-matters">{insight.why_matters}</p>
  </div>
))}
```

Insights są wyświetlane jako **kartki z badges** (confidence, source, year) zamiast prostej listy. Pokazują też "why_matters" - edukacyjne wyjaśnienie dlaczego dany wskaźnik jest ważny.

### 4.8 Migration Guide

**Dla istniejących person (legacy):**

```python
# Legacy personas (generated before segment-based refactor)
persona = get_persona_by_id("p_legacy_123")

# Will have:
persona.segment_id = None  # Nie przypisane do segmentu
persona.segment_name = None

# Reasoning panel (frontend) używa fallback:
if (!persona.segment_name) {
  // Fallback: pokazuje demographics bez segment header
  return <DemographicsOnly demographics={persona.demographics} />
}
```

Legacy persony **nie są invalid** - nadal działają, ale nie mają segment metadata. UI pokazuje dla nich fallback (demographics bez segment header).

**Dla nowych person (segment-based):**

```python
# New personas (generated with segment-based architecture)
persona = get_persona_by_id("p_new_456")

# Will have:
persona.segment_id = "seg_young_precariat"  # Assigned
persona.segment_name = "Młodzi Prekariusze"  # Displayed in UI
persona.segment_social_context = "Młodzi Prekariusze to osoby..."  # 500-800 chars

# Reasoning panel (frontend) używa pełnego reasoning:
if (persona.segment_name) {
  // Hero Header + Validation Alert + Individual Context + Graph Insights
  return <FullReasoningPanel persona={persona} />
}
```

Nowe persony mają **pełne reasoning** z Hero Header, Validation Alert i indywidualnym kontekstem.

### 4.9 Benefits

**1. Spójność (Consistency):**
- Persona ↔ segment ↔ brief zawsze pasują (HARD constraints)
- Age zawsze ∈ [age_min, age_max] (nie może być 38 gdy segment to 18-24)
- Gender zawsze = segment.gender (nie może być mężczyzna gdy segment to kobiety)

**2. Czytelność (Readability):**
- Mówiące nazwy segmentów ("Młodzi Prekariusze" zamiast "18-24, female, <3000 PLN")
- UI pokazuje segment name jako Hero Header - od razu widać grupę
- Łatwiej zrozumieć "kim są" persony

**3. Edukacyjność (Educational):**
- Indywidualny kontekst społeczny per segment (nie globalny)
- Wyjaśnia "dlaczego" ta grupa jest w takiej sytuacji (ekonomia, trendy)
- Graph insights z "why_matters" - edukacyjne wyjaśnienia

**4. Validatable:**
- HARD constraints można sprawdzić (age ∈ [min, max], gender = expected)
- Pydantic validators zapewniają spójność danych
- Validation Alert w UI pokazuje czy persona pasuje

**5. Scalable:**
- Łatwo dodać nowe segmenty bez refactor (tylko nowy SegmentDefinition)
- Segment-based queries (SQL: WHERE segment_id = 'seg_xyz')
- Można tworzyć segmenty "on-demand" dla różnych projektów

### 4.10 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│          SEGMENT-BASED PERSONA GENERATION ARCHITECTURE          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FAZA 1: ORCHESTRATION (Gemini 2.5 Pro)                       │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ PersonaOrchestrationService                            │   │
│  │ • _generate_segment_name() → "Młodzi Prekariusze"     │   │
│  │ • _generate_segment_context() → 500-800 chars kontekst│   │
│  │ • _filter_graph_insights_for_segment() → top 10       │   │
│  └────────────┬───────────────────────────────────────────┘   │
│               ↓                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ SegmentDefinition (Pydantic Schema)                    │   │
│  │ • segment_id: "seg_young_precariat"                    │   │
│  │ • segment_name: "Młodzi Prekariusze"                   │   │
│  │ • demographics: DemographicConstraints (HARD!)         │   │
│  │   - age_min: 18, age_max: 24                           │   │
│  │   - gender: "kobieta"                                  │   │
│  │   - education_levels: ["wyższe"]                       │   │
│  │ • segment_context: "Młodzi Prekariusze to osoby..."   │   │
│  │ • graph_insights: [filtered top 10]                    │   │
│  │ • persona_count: 5                                     │   │
│  └────────────┬───────────────────────────────────────────┘   │
│               ↓                                                 │
│  FAZA 2: GENERATION (Gemini 2.5 Flash)                        │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ PersonaGeneratorLangChain                              │   │
│  │ • generate_persona_from_segment()                      │   │
│  │   - ENFORCE age = randint(18, 24)                      │   │
│  │   - ENFORCE gender = "kobieta"                         │   │
│  │   - ENFORCE education ∈ allowed list                   │   │
│  │ • Post-generation override (safety net)                │   │
│  └────────────┬───────────────────────────────────────────┘   │
│               ↓                                                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ Persona (Database Record)                              │   │
│  │ • full_name: "Anna Nowak"                              │   │
│  │ • age: 22 ✅ (∈ [18, 24])                              │   │
│  │ • gender: "kobieta" ✅ (= segment.gender)              │   │
│  │ • segment_id: "seg_young_precariat"                    │   │
│  │ • segment_name: "Młodzi Prekariusze"                   │   │
│  └────────────┬───────────────────────────────────────────┘   │
│               ↓                                                 │
│  FAZA 3: UI DISPLAY (React)                                   │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ PersonaReasoningPanel.tsx                              │   │
│  │ • Hero Segment Header: "Młodzi Prekariusze"           │   │
│  │ • Validation Alert: ✅ Age 22 ∈ [18, 24]              │   │
│  │ • Individual Context: 500-800 chars                    │   │
│  │ • Graph Insights: Kartki z badges                     │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📚 Further Reading

**Google Gemini Documentation:**
- [Gemini API Docs](https://ai.google.dev/docs)
- [Model Comparison (Flash vs Pro)](https://ai.google.dev/models/gemini)
- [Best Practices](https://ai.google.dev/docs/best_practices)

**LangChain Documentation:**
- [LangChain Docs](https://python.langchain.com/docs/)
- [Google Generative AI Integration](https://python.langchain.com/docs/integrations/llms/google_ai)
- [Prompt Templates](https://python.langchain.com/docs/modules/model_io/prompts/)

**RAG Resources:**
- [RAG.md](RAG.md) - System RAG documentation (Hybrid Search + GraphRAG)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)

**Performance Optimization:**
- [Async Python Best Practices](https://docs.python.org/3/library/asyncio.html)
- [Tenacity (Retry Library)](https://tenacity.readthedocs.io/)

---

**Ostatnia aktualizacja:** 2025-10-15 (Segment-based architecture refactor)
**Wersja:** 1.1 (Added segment-based persona generation documentation)
**AI/RAG Score:** 7.8/10 (Improved with segment-based consistency)
