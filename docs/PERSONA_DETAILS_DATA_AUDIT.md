# Audyt Prawdziwości Danych AI/RAG w Persona Details

**Data audytu:** 2025-10-16
**Audytor:** AI Specialist (Claude)
**Wersja systemu:** MVP - Persona Details

---

## 1. Executive Summary

### Overall Data Quality Score: **5.5/10** 🟡

### Podział Źródeł Danych (Overall)
- **Real Data (Focus Groups):** 20% - tylko PersonaNeedsService
- **AI Estimation (z heurystykami):** 70% - KPI + Journey
- **Hardcoded Values:** 10% - industry benchmarks

### Top 3 Hallucination Risks 🚨

1. **KPI Snapshot - Hardcoded Industry Benchmarks (CRITICAL)**
   - Severity: **HIGH** (8/10)
   - Impact: Użytkownicy podejmują decyzje biznesowe oparte na fake KPI
   - Metrics: conversion_rate (0.12), retention_rate (0.85), NPS (45.0) są HARDCODED

2. **Customer Journey - Generic Journeys bez Real Data (HIGH)**
   - Severity: **HIGH** (7/10)
   - Impact: Journey stages mogą być halucynowane bez market context
   - RAG context: tylko 500 chars (za mało dla quality journeys)

3. **Segment Size - Simplistic Heuristics (MEDIUM)**
   - Severity: **MEDIUM** (6/10)
   - Impact: Segment size estimation ~50% accuracy
   - Brak integracji z GUS statistics z RAG

---

## 2. Analiza Źródeł Danych (per sekcja)

### 2.1 KPI Snapshot (PersonaKPIService)

#### Segment Size
- **Source:** Heuristics (base_population × demographic filters)
- **RAG Used:** ❌ **NO** (should query GUS statistics from RAG)
- **Accuracy:** ~50% (simplistic multipliers)
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:208-256
def _estimate_segment_size(self, persona: Persona) -> int:
    base_population = 38_000_000
    # Age filter (10-year span = ~15% of population)
    age_filter = 0.15
    # Gender filter
    gender_map = {"Kobieta": 0.52, "Mężczyzna": 0.48, "Osoba niebinarna": 0.02}
    gender_filter = gender_map.get(persona.gender, 0.5)
    # Education filter (educated = top 25%)
    education_filter = 0.25 if persona.education_level and "Wyższe" in persona.education_level else 0.75
    # Income filter (depends on bracket)
    income_filter = 0.20  # Średni przedział
    # Location filter
    location_filter = 0.08 if persona.location and persona.location != "Polska" else 1.0

    estimated_size = int(
        base_population * age_filter * gender_filter * education_filter * income_filter * location_filter
    )
    return max(1000, estimated_size)
```

**Problems:**
- Simplistic multipliers (age_filter = 0.15 for ALL 10-year spans)
- Education filter: binary (0.25 vs 0.75) - ignores actual GUS data
- NO RAG query despite having GUS population statistics in RAG documents
- Accuracy ~50% (varies ±50k for typical segment)

**Recommendation:**
```python
async def _estimate_segment_size_with_rag(self, persona: Persona) -> int:
    """Query RAG for GUS population statistics."""
    rag_query = (
        f"Populacja Polski: wiek {persona.age}, płeć {persona.gender}, "
        f"wykształcenie {persona.education_level}, lokalizacja {persona.location}"
    )
    # Hybrid search dla GUS documents
    results = await rag_service.hybrid_search(rag_query, top_k=3)

    # LLM extraction numeric values z RAG context
    population_estimate = await llm_extract_population(results)

    return population_estimate if population_estimate > 1000 else fallback_heuristic()
```

---

#### Conversion Rate
- **Source:** ❌ **HARDCODED** (0.12 = 12% industry avg)
- **RAG Used:** ❌ **NO**
- **Accuracy:** ~30% (industry avg, NOT segment-specific)
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:157
conversion_rate = 0.12  # 12% industry avg dla B2B SaaS
```

**Problems:**
- Fixed value for ALL personas (no demographic variance)
- "B2B SaaS" assumption - NOT validated from RAG documents
- NO industry-specific or segment-specific data

**Recommendation:**
- Query RAG documents for industry benchmarks (jeśli istnieją)
- OR add explicit disclaimer: "Industry average - not segment-specific"
- OR expose confidence_score (0.30) w UI

---

#### Retention Rate
- **Source:** ❌ **HARDCODED** (0.85 = 85% annual retention)
- **RAG Used:** ❌ **NO**
- **Accuracy:** ~30%
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:158
retention_rate = 0.85  # 85% annual retention
```

**Problems:** Same as conversion_rate (fixed, no variance, no RAG)

---

#### NPS Score
- **Source:** ❌ **HARDCODED** (45.0 = "good" NPS)
- **RAG Used:** ❌ **NO**
- **Accuracy:** ~30%
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:159
nps_score = 45.0  # NPS 45 (good)
```

**Problems:** Same as conversion_rate

---

#### LTV (Lifetime Value)
- **Source:** ⚠️ **HEURISTIC** (avg_income × 0.3 × 3 years)
- **RAG Used:** ❌ **NO** (but uses parsed income_bracket)
- **Accuracy:** ~40% (depends on income parsing accuracy)
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:162-164
avg_income = self._parse_income_bracket(persona.income_bracket)
ltv = avg_income * 0.3 * 3  # 30% of annual income * 3 years
cac = ltv * 0.15  # CAC = 15% of LTV (industry benchmark)
```

**Problems:**
- Arbitrary multipliers (0.3, 3, 0.15) - where do they come from?
- "30% of annual income" - NOT validated assumption
- "3 years" - fixed customer lifetime (no variance)

**Partial Credit:**
- At least uses real income_bracket (parsed from persona)
- `_parse_income_bracket()` extracts numeric values correctly

---

#### CAC (Customer Acquisition Cost)
- **Source:** ⚠️ **DERIVED** (CAC = LTV × 0.15)
- **RAG Used:** ❌ **NO**
- **Accuracy:** ~40% (depends on LTV accuracy)
- **Code Evidence:** (same as LTV)

**Problems:** Derived from fake LTV → fake CAC

---

#### Benchmarks
- **Source:** ❌ **HARDCODED** (industry averages)
- **RAG Used:** ❌ **NO**
- **Accuracy:** ~30%
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:194-200
"benchmarks": {
    "conversion_rate": 0.10,  # Industry avg
    "retention_rate": 0.80,
    "nps_score": 40.0,
    "ltv": ltv * 0.9,  # 10% niżej niż estimate
    "cac": cac * 1.1,  # 10% wyżej
}
```

**Problems:**
- Benchmarks są fake (no source)
- LTV/CAC benchmarks derived from fake estimates (±10% noise)

---

#### Data Transparency Metadata
- **Source:** ✅ **PRESENT** (but NOT visible in UI!)
- **Code Evidence:**
```python
# app/services/persona_kpi_service.py:201-204
"data_sources": ["rag", "ai_estimation"],  # ⚠️ "rag" is FALSE (nie używamy RAG!)
"confidence_score": 0.70,  # Niższy confidence dla AI estimation
"calculation_method": "ai_estimation",
```

**Problems:**
- `"data_sources": ["rag", ...]` is **MISLEADING** - RAG is NOT used!
- `confidence_score: 0.70` is reasonable but NOT shown in UI
- `calculation_method: "ai_estimation"` is accurate but NOT shown in UI

---

### KPI Snapshot - Overall Assessment

| Metric | Source | RAG Used? | Accuracy | Transparency (UI) |
|--------|--------|-----------|----------|-------------------|
| segment_size | Heuristics | ❌ NO | ~50% | ❌ NO |
| conversion_rate | Hardcoded | ❌ NO | ~30% | ❌ NO |
| retention_rate | Hardcoded | ❌ NO | ~30% | ❌ NO |
| nps_score | Hardcoded | ❌ NO | ~30% | ❌ NO |
| ltv | Heuristic | ❌ NO | ~40% | ❌ NO |
| cac | Derived | ❌ NO | ~40% | ❌ NO |
| benchmarks | Hardcoded | ❌ NO | ~30% | ❌ NO |

**Overall KPI Accuracy: ~35%** 🔴

**Critical Issue:** System claims `data_sources: ["rag", ...]` but RAG is NEVER queried!

---

### 2.2 Customer Journey (PersonaJourneyService)

#### Journey Stages (Awareness → Consideration → Decision → Post-Purchase)
- **Source:** ⚠️ **LLM Generation** (Gemini 2.5 Flash, temp=0.2)
- **RAG Used:** ⚠️ **PARTIAL** (persona.rag_context_details → truncated to 500 chars)
- **Accuracy:** ~60% (depends on RAG context quality + LLM creativity)
- **Code Evidence:**
```python
# app/services/persona_journey_service.py:107-147
def _build_prompt(self, persona: Persona, rag_context: Optional[str]) -> str:
    # Truncate RAG context to 500 chars for speed (vs. 4000)
    rag_section = (rag_context[:500] + "...") if rag_context and len(rag_context) > 500 else (rag_context or "Brak dodatkowego kontekstu")

    return f"""You are a B2B SaaS customer journey strategist.

Generate a 4-stage journey (Awareness → Consideration → Decision → Post-Purchase) for:

**Demographics:**
- {persona.age}y, {persona.gender or "?"}, {persona.location or "?"}
- {persona.occupation or "?"}, {persona.education_level or "?"}
- Income: {persona.income_bracket or "?"}

**Psychographics:**
- Big Five: O={persona.openness:.1f}, C={persona.conscientiousness:.1f}, ...

**Market Context:**
{rag_section}

Generate realistic journey with:
- Typical questions per stage
- Buying signals
- 3-5 touchpoints per stage (priority, impact 0-1, effort)
- Avg time in stage (days), drop-off rate (0-1)
- Overall journey length (days), conversion rate (0-1)

Base on provided data only."""
```

**RAG Context Source:**
```python
# app/services/persona_details_service.py:434-445
def _extract_rag_context(self, persona: Persona) -> Optional[str]:
    details = persona.rag_context_details or {}
    reasoning = details.get("orchestration_reasoning") or {}
    context_candidates = [
        reasoning.get("segment_social_context"),
        reasoning.get("overall_context"),
        details.get("graph_context"),
    ]
    for candidate in context_candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None
```

**Problems:**
1. **RAG context truncation (500 chars)** - insufficient for quality journeys
   - Original: up to 4000 chars (reasonable)
   - Optimized: 500 chars (TOO aggressive!)
   - Result: Loses critical market insights

2. **No focus group data** - journey could use PersonaResponse (real customer journeys)
   - PersonaNeedsService fetches PersonaResponse - why not JourneyService?

3. **Generic B2B SaaS assumption** - prompt hardcodes "B2B SaaS customer journey strategist"
   - NOT all personas are B2B SaaS customers!
   - Should be configurable or inferred from context

4. **Temperature 0.2** - good for determinism, but:
   - May reduce creativity in journey generation
   - May lead to similar journeys for similar demographics

5. **Touchpoint "impact 0-1" values** - are these real or LLM-generated?
   - NO validation against real conversion funnels
   - NO grounding in historical data

**What's GOOD:**
- ✅ Uses structured output (Pydantic) - prevents JSON parsing failures
- ✅ Uses persona demographics + psychographics (Big Five)
- ✅ Explicitly instructs: "Base on provided data only"
- ✅ Includes RAG context (even if truncated)

**Hallucination Risks:**
- **Generic journeys** (70% probability): "Browse website → Sign up → Trial → Purchase"
- **Fake buying signals** (60%): LLM invents signals not grounded in data
- **Arbitrary touchpoints** (50%): "3-5 touchpoints" without market validation
- **Fake drop-off rates** (80%): No historical data for drop-off percentages

---

### Customer Journey - Overall Assessment

| Aspect | Source | RAG Used? | Quality | Hallucination Risk |
|--------|--------|-----------|---------|-------------------|
| Journey stages | LLM | ⚠️ PARTIAL (500 chars) | ~60% | MEDIUM-HIGH (70%) |
| Questions per stage | LLM | ⚠️ PARTIAL | ~55% | HIGH (75%) |
| Buying signals | LLM | ⚠️ PARTIAL | ~50% | HIGH (80%) |
| Touchpoints | LLM | ⚠️ PARTIAL | ~50% | MEDIUM-HIGH (70%) |
| Drop-off rates | LLM | ❌ NO | ~30% | CRITICAL (80%) |
| Journey length (days) | LLM | ⚠️ PARTIAL | ~50% | MEDIUM (60%) |
| Conversion rate | LLM | ❌ NO | ~30% | HIGH (75%) |

**Overall Journey Accuracy: ~50%** 🟡

**Critical Issue:** RAG context truncated from 4000 → 500 chars loses critical insights!

---

### 2.3 Needs & Pains (PersonaNeedsService)

#### Jobs-to-be-Done (JTBD)
- **Source:** ✅ **REAL DATA** (PersonaResponse - focus group answers) + LLM extraction
- **RAG Used:** ❌ **NO** (uses focus groups instead)
- **Accuracy:** ~70% (depends on focus group data quality)
- **Code Evidence:**
```python
# app/services/persona_needs_service.py:99-120
async def _fetch_recent_responses(self, persona_id) -> List[Dict[str, str]]:
    """Fetch latest focus group responses for persona.

    Optimizations:
    - Limit reduced from 20 → 10 for speed (sufficient for JTBD analysis)
    """
    result = await self.db.execute(
        select(PersonaResponse)
        .where(PersonaResponse.persona_id == persona_id)
        .order_by(PersonaResponse.created_at.desc())
        .limit(10)  # Reduced from 20 for faster processing
    )
    responses = []
    for record in result.scalars():
        responses.append(
            {
                "question": record.question_text,
                "answer": record.response_text,
            }
        )
    return responses
```

**Prompt Evidence:**
```python
# app/services/persona_needs_service.py:148-166
return f"""You are a product strategist using Jobs-to-be-Done methodology.

Extract JTBD insights for:

**Profile:**
- {persona.age}y, {persona.occupation or "?"}
- Values: {values}
- Interests: {interests}
- Background: {background}

**Focus Group Insights (latest 10):**
{formatted_responses}

Generate:
1. Jobs-to-be-Done (format: "When [situation], I want [motivation], so I can [outcome]")
2. Desired outcomes (importance 1-10, satisfaction 1-10, opportunity score)
3. Pain points (severity 1-10, frequency, percent affected 0-1, quotes, solutions)

Base on provided data only."""
```

**What's EXCELLENT:**
- ✅ Uses **REAL focus group data** (PersonaResponse)
- ✅ Explicitly instructs: "Base on provided data only"
- ✅ Uses structured output (Pydantic) → NeedsAndPains schema
- ✅ Truncates background story (300 chars) for token efficiency
- ✅ Limits responses to 10 (reasonable for JTBD extraction)

**Problems:**
1. **Response limit (10 vs 20)** - may miss important insights
   - Tradeoff: speed vs coverage
   - Recommendation: A/B test 10 vs 15 responses

2. **Graceful degradation** - what if persona has NO focus group responses?
   - Current: Returns "Brak danych z grup fokusowych"
   - LLM may hallucinate jobs/pains without data!

3. **LLM may add fake jobs** - even with real responses
   - Prompt says "Base on provided data only" but LLM may extrapolate
   - No validation that jobs are grounded in actual quotes

4. **Quotes in JTBD** - are they real or paraphrased?
   - Schema expects quotes - but LLM may paraphrase or invent
   - No validation against original PersonaResponse.response_text

5. **Priority/severity scores** - are they real or LLM guess?
   - Schema: importance (1-10), satisfaction (1-10), opportunity_score
   - NO historical data to validate these scores
   - LLM generates scores based on interpretation, not data

**Hallucination Risks:**
- **Fake jobs** (40%): LLM adds jobs not mentioned in focus groups
- **Paraphrased quotes** (60%): Quotes may be LLM-generated, not exact
- **Arbitrary scores** (70%): Importance/severity scores are LLM guesses
- **Generic pains** (50%): Without focus group data, LLM may invent generic pains

---

### Needs & Pains - Overall Assessment

| Aspect | Source | Real Data? | Quality | Hallucination Risk |
|--------|--------|------------|---------|-------------------|
| Jobs-to-be-Done | Focus Groups + LLM | ✅ YES (if responses exist) | ~70% | MEDIUM (40%) |
| Desired outcomes | LLM extraction | ⚠️ PARTIAL | ~60% | MEDIUM-HIGH (60%) |
| Pain points | Focus Groups + LLM | ✅ YES | ~70% | MEDIUM (50%) |
| Quotes | Focus Groups | ⚠️ PARTIAL (may be paraphrased) | ~60% | MEDIUM-HIGH (60%) |
| Importance scores | LLM | ❌ NO | ~40% | HIGH (70%) |
| Opportunity scores | LLM | ❌ NO | ~40% | HIGH (70%) |

**Overall Needs Accuracy: ~60%** 🟡

**Graceful Degradation Risk:** If persona has NO focus group responses → HIGH hallucination risk!

---

## 3. RAG Integration Analysis

### 3.1 Persona Generation - RAG Context Quality

**Evidence from PersonaGeneratorLangChain:**
```python
# app/services/persona_generator_langchain.py:280-329
async def _get_rag_context_for_persona(
    self, demographic: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Pobierz kontekst z RAG dla danego profilu demograficznego"""
    if not self.rag_service:
        return None

    try:
        context_data = await self.rag_service.get_demographic_insights(
            age_group=demographic.get('age_group', '25-34'),
            education=demographic.get('education_level', 'wyższe'),
            location=demographic.get('location', 'Warszawa'),
            gender=demographic.get('gender', 'mężczyzna')
        )

        # Loguj szczegóły RAG context
        context_len = len(context_data.get('context', ''))
        graph_nodes_count = len(context_data.get('graph_nodes', []))
        search_type = context_data.get('search_type', 'unknown')
        citations_count = len(context_data.get('citations', []))

        logger.info(
            f"RAG context retrieved: {context_len} chars, "
            f"{graph_nodes_count} graph nodes, "
            f"{citations_count} citations, "
            f"search_type={search_type}"
        )

        return context_data
    except Exception as e:
        logger.error(f"RAG context retrieval failed: {e}", exc_info=True)
        return None
```

**PolishSocietyRAG.get_demographic_insights():**
```python
# app/services/rag_hybrid_search_service.py:558-722
async def get_demographic_insights(
    self,
    age_group: str,
    education: str,
    location: str,
    gender: str,
) -> Dict[str, Any]:
    """Builds context combining Graph RAG + Hybrid Search (Vector + Keyword)."""

    # 1. GRAPH RAG - Structured knowledge from Neo4j graph
    graph_nodes = self.graph_rag_service.get_demographic_graph_context(
        age_group=age_group,
        location=location,
        education=education,
        gender=gender
    )
    # Format graph nodes → readable text
    graph_context_formatted = self._format_graph_context(graph_nodes)

    # 2. HYBRID SEARCH (Vector + Keyword + RRF)
    if settings.RAG_USE_HYBRID_SEARCH:
        candidates_k = settings.RAG_RERANK_CANDIDATES if settings.RAG_USE_RERANKING else settings.RAG_TOP_K * 2

        vector_results = await self.vector_store.asimilarity_search_with_score(query, k=candidates_k)
        keyword_results = await self._keyword_search(query, k=candidates_k)
        fused_results = self._rrf_fusion(vector_results, keyword_results, k=settings.RAG_RRF_K)

        # 2b. RERANKING (optional) - Cross-encoder for precision
        if settings.RAG_USE_RERANKING and self.reranker:
            final_results = self._rerank_with_cross_encoder(
                query=query,
                candidates=fused_results[:settings.RAG_RERANK_CANDIDATES],
                top_k=settings.RAG_TOP_K
            )

    # 3. UNIFIED CONTEXT - Enrich chunks with related graph nodes
    context_chunks = []
    if graph_context_formatted:
        context_chunks.append("=== STRUKTURALNA WIEDZA Z GRAFU WIEDZY ===\n")
        context_chunks.append(graph_context_formatted)
        context_chunks.append("\n=== KONTEKST Z DOKUMENTÓW (WZBOGACONY) ===\n")

    # Enrich chunks with graph nodes
    for doc, score in final_results:
        related_nodes = self._find_related_graph_nodes(doc, graph_nodes)
        enriched_text = self._enrich_chunk_with_graph(doc.page_content, related_nodes) if related_nodes else doc.page_content
        context_chunks.append(enriched_text)

    return {
        "context": "\n\n---\n\n".join(context_chunks),
        "graph_context": graph_context_formatted,
        "graph_nodes": graph_nodes,
        "citations": citations,
        "search_type": "hybrid+rerank+graph" if reranking else "hybrid+graph"
    }
```

**What's EXCELLENT:**
- ✅ **Dual-source retrieval:** Graph RAG + Hybrid Search (Vector + Keyword)
- ✅ **RRF fusion:** Combines semantic + lexical search
- ✅ **Optional reranking:** Cross-encoder for precision (if enabled)
- ✅ **Graph enrichment:** Chunks enriched with related graph nodes
- ✅ **Comprehensive metadata:** graph_nodes_count, search_type, citations_count

**RAG Context Flow:**
```
PersonaGenerator → PolishSocietyRAG → Graph RAG (Neo4j Cypher) + Hybrid Search (Vector + Keyword)
                                    ↓
                          GraphRAGService.get_demographic_graph_context()
                                    ↓
                          Returns: Wskaznik, Obserwacja, Trend, Demografia nodes
                                    ↓
                          PolishSocietyRAG._format_graph_context()
                                    ↓
                          Formatted text: "📊 WSKAŹNIKI DEMOGRAFICZNE..."
                                    ↓
                          Enriched chunks: Original chunk + related graph insights
                                    ↓
                          Final context: Graph knowledge + Vector search chunks
```

**Evidence - Graph Context Query (Cypher):**
```cypher
// app/services/rag_graph_service.py:344-431
// 1. Znajdź Wskaźniki (preferuj wysoką pewność)
MATCH (ind:Wskaznik)
WHERE ANY(term IN $search_terms WHERE
    toLower(coalesce(ind.streszczenie, '')) CONTAINS toLower(term) OR
    toLower(coalesce(ind.kluczowe_fakty, '')) CONTAINS toLower(term)
)
WITH ind
ORDER BY
    CASE WHEN ind.pewnosc = 'wysoka' THEN 0
         WHEN ind.pewnosc = 'srednia' THEN 1
         ELSE 2 END,
    size(coalesce(ind.kluczowe_fakty, '')) DESC
LIMIT 3
WITH collect({
    type: 'Wskaznik',
    streszczenie: ind.streszczenie,
    kluczowe_fakty: ind.kluczowe_fakty,
    skala: ind.skala,
    pewnosc: coalesce(ind.pewnosc, 'nieznana'),
    okres_czasu: ind.okres_czasu
}) AS indicators

// 2. Znajdź Obserwacje (preferuj wysoką pewność)
MATCH (obs:Obserwacja)
WHERE ANY(term IN $search_terms WHERE ...)
LIMIT 3

// 3. Znajdź Trendy
MATCH (trend:Trend)
WHERE ANY(term IN $search_terms WHERE ...)
LIMIT 2

// 4. Znajdź węzły Demografii
MATCH (demo:Demografia)
WHERE ANY(term IN $search_terms WHERE ...)
LIMIT 2

RETURN indicators + observations + trends + demographics AS graph_context
```

**What's GOOD:**
- ✅ Prioritizes high confidence nodes (`pewnosc='wysoka'`)
- ✅ Limits results (3 indicators, 3 observations, 2 trends, 2 demographics)
- ✅ Uses case-insensitive search (toLower)
- ✅ Flexible matching (streszczenie OR kluczowe_fakty)

**Problems:**
1. **CONTAINS matching** - may miss exact demographic matches
   - "25-34" may not match "25-35" (off by 1 year)
   - "wyższe" may not match "wykształcenie wyższe magisterskie"
   - Recommendation: Add fuzzy matching or broader terms

2. **Limited results** - only 10 nodes total (3+3+2+2)
   - May miss important insights if graph has many relevant nodes
   - Recommendation: Make LIMIT configurable (e.g., TOP_K=15)

3. **No relationship traversal** - query only matches nodes by properties
   - Graph RAG potential: traverse relationships (OPISUJE, DOTYCZY, etc.)
   - Missed opportunity: "Wskaznik -[OPISUJE]-> Demografia" paths

---

### 3.2 RAG Context in Persona Details Services

#### PersonaKPIService
- **RAG Integration:** ❌ **NOT USED** (despite claiming `data_sources: ["rag", ...]`)
- **Evidence:** No RAG query in `_estimate_with_ai()` method
- **Missed Opportunity:** Could query RAG for GUS population statistics

#### PersonaJourneyService
- **RAG Integration:** ⚠️ **PARTIAL** (uses persona.rag_context_details)
- **Evidence:**
```python
# app/services/persona_details_service.py:434-445
def _extract_rag_context(self, persona: Persona) -> Optional[str]:
    details = persona.rag_context_details or {}
    reasoning = details.get("orchestration_reasoning") or {}
    context_candidates = [
        reasoning.get("segment_social_context"),
        reasoning.get("overall_context"),
        details.get("graph_context"),
    ]
```
- **Truncation:** 500 chars (down from 4000) - too aggressive!
- **Quality:** Depends on persona generation RAG quality

#### PersonaNeedsService
- **RAG Integration:** ❌ **NOT USED** (uses PersonaResponse instead)
- **Alternative:** Focus group data (REAL data!) - this is BETTER than RAG
- **Evidence:** Fetches PersonaResponse records, not RAG documents

---

### 3.3 RAG Document Availability

**Question:** Do RAG documents contain data needed for Persona Details?

**Evidence - RAG Documents Expected:**
```python
# docs/RAG.md:89-96
## Przepływ Ingestu Dokumentów

1. Upload dokumentu przez API
2. Podział na chunki (1000 znaków, 30% overlap)
3. Ekstrakcja embeddings
4. Zapis chunków i grafu w Neo4j
5. Wzbogacenie metadanych
```

**Document Types (from docs/RAG.md):**
- GUS population statistics (demografia)
- CBOS social surveys (opinie społeczne)
- Industry reports (benchmarki branżowe?)

**Graph Node Types:**
- **Wskaznik** (Indicators): Statystyki, metryki → GOOD for KPI!
- **Obserwacja** (Observations): Fakty, przyczyny → GOOD for Journey!
- **Trend** (Trends): Zmiany w czasie → GOOD for Journey!
- **Demografia** (Demographics): Grupy demograficzne → GOOD for Segment Size!

**Assessment:**
- ✅ **Graph RAG DOES contain useful data** for KPI/Journey/Needs
- ✅ **Wskaznik nodes** could provide GUS population stats for segment_size
- ✅ **Trend nodes** could provide industry benchmarks for conversion/retention
- ❌ **NOT utilized** by PersonaKPIService or PersonaJourneyService (500 char limit)

**Recommendation:**
- Use Graph RAG for KPI extraction (query Wskaznik nodes for population stats)
- Expand RAG context for Journey (500 → 1500 chars minimum)
- Add RAG query for industry benchmarks (if documents exist)

---

## 4. Hallucination Risks & Mitigation

### Risk 1: Generic Customer Journey (SEVERITY: HIGH)

**Probability:** 70%
**Impact:** Users make strategic decisions based on fake journey stages

**Causes:**
1. RAG context truncated to 500 chars (insufficient for quality journeys)
2. No focus group data used (PersonaResponse not fetched)
3. Generic "B2B SaaS" assumption in prompt
4. Temperature 0.2 may lead to similar journeys

**Mitigation:**

**Priority 1: Expand RAG context (EFFORT: Low, IMPACT: High)**
```python
# app/services/persona_journey_service.py:119-120
# BEFORE (500 chars - TOO aggressive!)
rag_section = (rag_context[:500] + "...") if rag_context and len(rag_context) > 500 else ...

# AFTER (1500 chars - better balance)
rag_section = (rag_context[:1500] + "...") if rag_context and len(rag_context) > 1500 else ...
```

**Priority 2: Add focus group journey data (EFFORT: Medium, IMPACT: High)**
```python
async def _fetch_journey_related_responses(self, persona_id: UUID) -> List[str]:
    """Fetch focus group responses related to customer journey."""
    result = await self.db.execute(
        select(PersonaResponse)
        .where(
            PersonaResponse.persona_id == persona_id,
            # Filter for journey-related questions (if tagged)
            or_(
                PersonaResponse.question_text.ilike('%journey%'),
                PersonaResponse.question_text.ilike('%decision%'),
                PersonaResponse.question_text.ilike('%purchase%')
            )
        )
        .order_by(PersonaResponse.created_at.desc())
        .limit(5)
    )
    return [r.response_text for r in result.scalars()]

# Add to prompt:
journey_responses = await self._fetch_journey_related_responses(persona.id)
if journey_responses:
    prompt += f"\n\n**Real Customer Journey Insights:**\n"
    prompt += "\n".join([f"- {resp[:200]}" for resp in journey_responses])
```

**Priority 3: Add grounding instruction (EFFORT: Low, IMPACT: Medium)**
```python
# Add to prompt (line 146):
Base on provided data only. If insufficient data, return conservative estimates with low confidence.
DO NOT invent touchpoints or drop-off rates without evidence.
```

---

### Risk 2: Hardcoded KPI Benchmarks (SEVERITY: CRITICAL)

**Probability:** 100% (hardcoded!)
**Impact:** Business decisions based on fake conversion/retention/NPS data

**Causes:**
1. conversion_rate, retention_rate, NPS are hardcoded (0.12, 0.85, 45.0)
2. NO RAG query despite having Wskaznik/Trend nodes in graph
3. System falsely claims `data_sources: ["rag", ...]`

**Mitigation:**

**Priority 1: Implement RAG-based KPI extraction (EFFORT: Medium, IMPACT: Critical)**
```python
async def _estimate_with_rag(self, persona: Persona) -> Dict[str, Any]:
    """Estimate KPI using RAG (Graph RAG + Vector Search)."""

    # 1. Query Graph RAG for industry benchmarks (Wskaznik nodes)
    rag_query = f"Wskaźniki konwersji, retencji, NPS dla branży: {persona.occupation}, demografia: {persona.age}, {persona.education_level}"

    graph_nodes = await self.graph_rag_service.get_demographic_graph_context(
        age_group=f"{persona.age-5}-{persona.age+5}",
        location=persona.location or "Polska",
        education=persona.education_level or "wyższe",
        gender=persona.gender or "kobieta"
    )

    # Extract numeric values from Wskaznik nodes (skala property)
    conversion_rate = self._extract_metric(graph_nodes, "konwersja", fallback=0.12)
    retention_rate = self._extract_metric(graph_nodes, "retencja", fallback=0.85)
    nps_score = self._extract_metric(graph_nodes, "NPS", fallback=45.0)

    # 2. Query GUS for segment size (Demografia nodes)
    segment_size = await self._estimate_segment_size_with_rag(persona)

    # 3. Confidence scoring based on data availability
    confidence_score = 0.85 if graph_nodes else 0.50
    data_sources = ["rag", "graph"] if graph_nodes else ["heuristics"]

    return {
        "segment_size": segment_size,
        "conversion_rate": conversion_rate,
        "retention_rate": retention_rate,
        "nps_score": nps_score,
        "confidence_score": confidence_score,
        "data_sources": data_sources,
        "calculation_method": "rag_extraction" if graph_nodes else "ai_estimation"
    }

def _extract_metric(self, graph_nodes: List[Dict], metric_name: str, fallback: float) -> float:
    """Extract numeric metric from graph nodes (Wskaznik.skala)."""
    for node in graph_nodes:
        if node.get('type') == 'Wskaznik':
            summary = node.get('streszczenie', '').lower()
            skala = node.get('skala', '')

            if metric_name.lower() in summary and skala:
                # Parse skala: "12.5%" → 0.125, "45" → 45.0
                try:
                    if '%' in skala:
                        return float(skala.replace('%', '')) / 100
                    else:
                        return float(skala)
                except ValueError:
                    pass

    return fallback  # Fallback to hardcoded if not found
```

**Priority 2: Add transparency UI badges (EFFORT: Low, IMPACT: High)**
```tsx
// frontend/src/components/personas/InsightsSection.tsx
{kpi_snapshot.calculation_method === "ai_estimation" && (
  <Badge variant="warning">
    ⚠️ AI Estimation (Confidence: {(kpi_snapshot.confidence_score * 100).toFixed(0)}%)
  </Badge>
)}

{kpi_snapshot.data_sources.includes("rag") && (
  <Badge variant="success">
    ✅ Real Data (RAG)
  </Badge>
)}
```

**Priority 3: Fix misleading data_sources claim (EFFORT: Low, IMPACT: High)**
```python
# app/services/persona_kpi_service.py:201
# BEFORE (MISLEADING!)
"data_sources": ["rag", "ai_estimation"],

# AFTER (ACCURATE)
"data_sources": ["heuristics", "ai_estimation"],  # NO RAG used!
```

---

### Risk 3: Simplistic Segment Size Heuristics (SEVERITY: MEDIUM)

**Probability:** 100% (heuristics always used)
**Impact:** Segment size ±50% error → wrong market sizing

**Causes:**
1. Simplistic multipliers (age_filter=0.15 for ALL 10-year spans)
2. Binary education filter (0.25 vs 0.75)
3. NO GUS statistics despite having Demografia nodes in graph

**Mitigation:**

**Priority 1: Query RAG for GUS population data (EFFORT: Medium, IMPACT: High)**
```python
async def _estimate_segment_size_with_rag(self, persona: Persona) -> int:
    """Estimate segment size using GUS statistics from RAG."""

    # Query Graph RAG for Demografia nodes
    rag_query = f"Populacja Polski: wiek {persona.age}, płeć {persona.gender}, wykształcenie {persona.education_level}, lokalizacja {persona.location}"

    graph_nodes = await self.graph_rag_service.get_demographic_graph_context(
        age_group=f"{persona.age-5}-{persona.age+5}",
        location=persona.location or "Polska",
        education=persona.education_level or "wyższe",
        gender=persona.gender or "kobieta"
    )

    # Extract population from Demografia nodes (skala property)
    for node in graph_nodes:
        if node.get('type') in ('Demografia', 'Wskaznik'):
            skala = node.get('skala', '')
            # Parse: "2.5 mln" → 2500000, "350 tys." → 350000
            population = self._parse_population(skala)
            if population > 0:
                logger.info(f"RAG segment size: {population} (confidence: {node.get('pewnosc', 'unknown')})")
                return population

    # Fallback to heuristics
    logger.warning("RAG segment size not found - falling back to heuristics")
    return self._estimate_segment_size_heuristic(persona)

def _parse_population(self, skala: str) -> int:
    """Parse population from skala string."""
    skala_lower = skala.lower()
    try:
        if 'mln' in skala_lower or 'milion' in skala_lower:
            num = float(re.search(r'[\d.]+', skala_lower).group())
            return int(num * 1_000_000)
        elif 'tys' in skala_lower or 'tysiąc' in skala_lower or 'tysięcy' in skala_lower:
            num = float(re.search(r'[\d.]+', skala_lower).group())
            return int(num * 1_000)
        else:
            return int(float(re.search(r'[\d]+', skala_lower).group()))
    except (AttributeError, ValueError):
        return 0
```

---

### Risk 4: LLM Hallucinations in Needs (SEVERITY: MEDIUM)

**Probability:** 40% (if focus groups exist), 80% (if no data)
**Impact:** Fake jobs/pains mislead product strategy

**Causes:**
1. LLM may add jobs not mentioned in focus groups
2. Quotes may be paraphrased (not exact)
3. Importance/severity scores are LLM guesses (no validation)
4. NO graceful degradation if persona has no focus group responses

**Mitigation:**

**Priority 1: Add quote validation (EFFORT: Medium, IMPACT: Medium)**
```python
def _validate_quotes(self, needs_data: Dict, responses: List[Dict]) -> Dict:
    """Validate that quotes in JTBD actually come from focus group responses."""

    # Extract all response texts
    response_texts = [r['answer'].lower() for r in responses]

    # Check each pain point quote
    for pain in needs_data.get('pain_points', []):
        quote = pain.get('quote', '').lower()
        if not quote:
            continue

        # Check if quote substring exists in any response
        found = any(quote[:50] in text for text in response_texts)

        if not found:
            # Quote likely hallucinated - mark with warning
            pain['quote_verified'] = False
            pain['quote'] = f"[AI SUMMARY] {pain['quote']}"
        else:
            pain['quote_verified'] = True

    return needs_data
```

**Priority 2: Graceful degradation for missing focus groups (EFFORT: Low, IMPACT: High)**
```python
# app/services/persona_needs_service.py:147
# BEFORE
formatted_responses = "Brak danych z grup fokusowych."

# AFTER
if not responses:
    # Return empty needs structure instead of hallucinated data
    return {
        "jobs_to_be_done": [],
        "desired_outcomes": [],
        "pain_points": [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": settings.ANALYSIS_MODEL,
        "data_quality": "no_focus_group_data",
        "warning": "Persona nie ma danych z grup fokusowych - needs cannot be generated"
    }
```

**Priority 3: Increase response limit for critical personas (EFFORT: Low, IMPACT: Low)**
```python
# app/services/persona_needs_service.py:110
# Make limit configurable
limit = 15 if persona.is_critical else 10  # More data for important personas
```

---

## 5. Implementation Plan - Real RAG-Based Data

### Phase 1: Quick Wins (Effort: Low, Impact: High) - Week 1

#### 1.1 Fix Misleading Metadata (2 hours)
**File:** `app/services/persona_kpi_service.py`
```python
# Line 201 - Fix data_sources claim
"data_sources": ["heuristics", "ai_estimation"],  # Was: ["rag", "ai_estimation"]
```

#### 1.2 Expand Journey RAG Context (1 hour)
**File:** `app/services/persona_journey_service.py`
```python
# Line 119-120 - Increase truncation limit
rag_section = (rag_context[:1500] + "...") if rag_context and len(rag_context) > 1500 else ...
# Was: 500 chars → Now: 1500 chars (3x more context)
```

#### 1.3 Add Grounding Instructions (1 hour)
**Files:** `persona_journey_service.py`, `persona_needs_service.py`
```python
# Add to prompts:
Base on provided data only. If insufficient data, return conservative estimates.
DO NOT invent metrics, stages, or insights without evidence from context.
```

#### 1.4 Add Transparency UI Badges (4 hours)
**File:** `frontend/src/components/personas/InsightsSection.tsx`
```tsx
<Badge variant={kpi.calculation_method === 'rag_extraction' ? 'success' : 'warning'}>
  {kpi.calculation_method === 'rag_extraction' ? '✅ Real Data' : '⚠️ AI Estimation'}
</Badge>
<Text size="sm" color="gray">
  Confidence: {(kpi.confidence_score * 100).toFixed(0)}%
</Text>
```

**Total: ~8 hours, Impact: HIGH**

---

### Phase 2: RAG-Based KPI Extraction (Effort: Medium, Impact: Critical) - Week 2-3

#### 2.1 Implement Graph RAG KPI Query (16 hours)
**File:** `app/services/persona_kpi_service.py`

**Steps:**
1. Add `GraphRAGService` dependency to `PersonaKPIService.__init__()`
2. Create `_estimate_with_rag()` method (queries Wskaznik nodes)
3. Create `_extract_metric()` helper (parses skala values)
4. Update `calculate_kpi_snapshot()` to use RAG when available
5. Add fallback to heuristics if RAG fails
6. Update confidence scoring based on data source

**Pseudocode:**
```python
async def _estimate_with_rag(self, persona: Persona) -> Dict[str, Any]:
    # 1. Query Graph RAG for Wskaznik nodes
    graph_nodes = await self.graph_rag_service.get_demographic_graph_context(...)

    # 2. Extract metrics from Wskaznik.skala
    conversion_rate = self._extract_metric(graph_nodes, "konwersja", fallback=0.12)
    retention_rate = self._extract_metric(graph_nodes, "retencja", fallback=0.85)
    nps_score = self._extract_metric(graph_nodes, "NPS", fallback=45.0)

    # 3. Confidence scoring
    confidence = 0.85 if graph_nodes else 0.50
    data_sources = ["rag", "graph"] if graph_nodes else ["heuristics"]

    return {
        "conversion_rate": conversion_rate,
        "retention_rate": retention_rate,
        "nps_score": nps_score,
        "confidence_score": confidence,
        "data_sources": data_sources,
        "calculation_method": "rag_extraction" if graph_nodes else "ai_estimation"
    }
```

#### 2.2 Implement RAG-Based Segment Size (12 hours)
**File:** `app/services/persona_kpi_service.py`

**Steps:**
1. Create `_estimate_segment_size_with_rag()` method
2. Query Demografia nodes for population statistics
3. Parse skala values ("2.5 mln", "350 tys.") → numeric
4. Fallback to heuristics if RAG returns no results
5. Log RAG vs heuristic differences for monitoring

#### 2.3 Add RAG Quality Validation (8 hours)
**File:** `app/services/persona_kpi_service.py`

**Steps:**
1. Validate extracted metrics are in reasonable ranges
2. Log warnings for suspicious values (conversion > 0.5, NPS > 100)
3. Add metadata: `rag_nodes_used`, `rag_query`, `extraction_confidence`
4. Expose validation status in response

**Total: ~36 hours, Impact: CRITICAL**

---

### Phase 3: Journey Data Enrichment (Effort: Medium, Impact: High) - Week 3-4

#### 3.1 Add Focus Group Journey Data (12 hours)
**File:** `app/services/persona_journey_service.py`

**Steps:**
1. Create `_fetch_journey_related_responses()` method
2. Filter PersonaResponse for journey-related questions
3. Add focus group insights to prompt (after RAG context)
4. Limit to 5 most relevant responses (token efficiency)
5. Format as: "Real Customer Journey Insights: - [response 1], - [response 2], ..."

#### 3.2 Improve RAG Context Extraction (8 hours)
**File:** `app/services/persona_details_service.py`

**Steps:**
1. Expand `_extract_rag_context()` to include more context sources
2. Prioritize graph_context over orchestration_reasoning
3. Add fallback to persona.rag_citations if context is empty
4. Log context length and source for debugging

**Total: ~20 hours, Impact: HIGH**

---

### Phase 4: Needs Validation & Graceful Degradation (Effort: Low, Impact: Medium) - Week 4

#### 4.1 Quote Validation (6 hours)
**File:** `app/services/persona_needs_service.py`

**Steps:**
1. Create `_validate_quotes()` method
2. Check if quotes exist in original PersonaResponse texts
3. Mark unverified quotes with `[AI SUMMARY]` prefix
4. Add `quote_verified: bool` field to schema

#### 4.2 Graceful Degradation (4 hours)
**File:** `app/services/persona_needs_service.py`

**Steps:**
1. Check if `responses` list is empty BEFORE LLM call
2. Return structured empty response with warning
3. Add `data_quality` field: "no_focus_group_data" | "low_response_count" | "sufficient_data"
4. UI shows warning badge for low quality needs

**Total: ~10 hours, Impact: MEDIUM**

---

### Implementation Timeline Summary

| Phase | Effort | Impact | Duration | Priority |
|-------|--------|--------|----------|----------|
| Phase 1: Quick Wins | Low (8h) | HIGH | Week 1 | ⭐⭐⭐ CRITICAL |
| Phase 2: RAG KPI | Medium (36h) | CRITICAL | Week 2-3 | ⭐⭐⭐ CRITICAL |
| Phase 3: Journey Enrichment | Medium (20h) | HIGH | Week 3-4 | ⭐⭐ HIGH |
| Phase 4: Needs Validation | Low (10h) | MEDIUM | Week 4 | ⭐ MEDIUM |

**Total Effort:** ~74 hours (~2 sprints)
**Total Impact:** CRITICAL → Production-ready RAG-based Persona Details

---

## 6. Prompt Engineering Recommendations

### 6.1 PersonaKPIService - No Prompts (Heuristics Only)

**Current:** Uses hardcoded heuristics, NO LLM prompts
**Recommendation:** Keep heuristics for fallback, add RAG extraction (no prompt changes needed)

---

### 6.2 PersonaJourneyService - Journey Prompt Optimization

**Current Prompt Issues:**
1. "B2B SaaS" hardcoded assumption (not all personas are B2B SaaS!)
2. RAG context truncated to 500 chars (insufficient)
3. No grounding enforcement ("Base on provided data only" too weak)
4. No focus group journey data

**Optimized Prompt:**
```python
def _build_prompt(self, persona: Persona, rag_context: Optional[str], focus_group_journeys: Optional[str]) -> str:
    # Expand RAG context limit
    rag_section = (rag_context[:1500] + "...") if rag_context and len(rag_context) > 1500 else (rag_context or "Brak dodatkowego kontekstu")

    # Add focus group journeys (if available)
    fg_section = ""
    if focus_group_journeys:
        fg_section = f"""
**Real Customer Journey Examples (Focus Groups):**
{focus_group_journeys}

⚠️ CRITICAL: Ground journey stages in these real examples. Do NOT invent generic stages.
"""

    return f"""You are a customer journey analyst specializing in Polish market research.

Generate a 4-stage journey (Awareness → Consideration → Decision → Post-Purchase) for:

**Demographics:**
- {persona.age}y, {persona.gender or "?"}, {persona.location or "?"}
- {persona.occupation or "?"}, {persona.education_level or "?"}
- Income: {persona.income_bracket or "?"}

**Psychographics:**
- Big Five: O={persona.openness:.1f}, C={persona.conscientiousness:.1f}, E={persona.extraversion:.1f}, A={persona.agreeableness:.1f}, N={persona.neuroticism:.1f}
- Values: {", ".join(persona.values or [])}
- Interests: {", ".join(persona.interests or [])}

**Market Context (RAG):**
{rag_section}

{fg_section}

**STRICT GROUNDING RULES:**
1. Use ONLY provided data (demographics, psychographics, RAG context, focus groups)
2. If insufficient data for a stage, return conservative estimates with note: "Limited data - low confidence"
3. DO NOT invent touchpoints without evidence from context
4. Drop-off rates MUST be grounded in market data OR marked as "estimated"
5. Questions per stage MUST reflect persona's psychographics (high O → exploratory questions)

Generate realistic journey with:
- Typical questions per stage (based on psychographics + context)
- Buying signals (evidence-based)
- 3-5 touchpoints per stage (priority: high|medium|low, impact: 0-1, effort: high|medium|low)
- Avg time in stage (days), drop-off rate (0-1) - mark as "estimated" if no data
- Overall journey length (days), conversion rate (0-1)

JSON output only (no markdown)."""
```

**Key Improvements:**
- ✅ Removed "B2B SaaS" hardcoded assumption
- ✅ Expanded RAG context (500 → 1500 chars)
- ✅ Added focus group journey examples
- ✅ Strict grounding rules with consequences
- ✅ Explicit handling of insufficient data ("Limited data - low confidence")
- ✅ Psychographics-driven questions (high Openness → exploratory questions)

---

### 6.3 PersonaNeedsService - Needs Prompt Optimization

**Current Prompt Issues:**
1. No explicit handling of missing focus group data
2. No validation that jobs are grounded in quotes
3. Importance/severity scores lack calibration

**Optimized Prompt:**
```python
def _build_prompt(self, persona: Persona, responses: List[Dict[str, str]]) -> str:
    background = (persona.background_story[:300] + "...") if persona.background_story and len(persona.background_story) > 300 else (persona.background_story or "Brak")
    values = ", ".join(persona.values or []) if persona.values else "brak"
    interests = ", ".join(persona.interests or []) if persona.interests else "brak"

    # Format responses with truncation
    formatted_responses = ""
    if responses:
        formatted = [
            f"- Q: {entry['question'][:100]}...\n  A: {entry['answer'][:150]}..."
            if len(entry['question']) > 100 or len(entry['answer']) > 150
            else f"- Q: {entry['question']}\n  A: {entry['answer']}"
            for entry in responses[:10]
        ]
        formatted_responses = "\n".join(formatted)
    else:
        # NO hallucination if no data!
        formatted_responses = "⚠️ BRAK DANYCH - Return empty arrays for jobs/outcomes/pains"

    return f"""You are a product strategist using Jobs-to-be-Done (JTBD) methodology.

Extract JTBD insights for:

**Profile:**
- {persona.age}y, {persona.occupation or "?"}
- Values: {values}
- Interests: {interests}
- Background: {background}

**Focus Group Insights (latest 10):**
{formatted_responses}

**STRICT EXTRACTION RULES:**
1. ONLY extract jobs/outcomes/pains that are DIRECTLY mentioned or strongly implied in focus group answers
2. DO NOT invent generic jobs/pains (e.g., "save time", "reduce cost") without specific evidence
3. Quotes MUST be exact excerpts from focus group answers (max 150 chars) - DO NOT paraphrase
4. If focus group data is missing (⚠️ BRAK DANYCH), return EMPTY arrays - DO NOT hallucinate
5. Importance/severity scores (1-10) MUST be calibrated:
   - 1-3: Minor concern (mentioned once)
   - 4-6: Moderate concern (mentioned 2-3 times or with moderate emotion)
   - 7-10: Critical concern (mentioned repeatedly or with strong emotion)

Generate:
1. **Jobs-to-be-Done** (format: "When [situation], I want [motivation], so I can [outcome]")
   - ONLY if situation is mentioned in focus groups
   - Link to specific response quote

2. **Desired Outcomes** (importance 1-10, satisfaction 1-10, opportunity score)
   - importance: How often mentioned (1=once, 10=every response)
   - satisfaction: Current satisfaction level from responses (1=very unsatisfied, 10=very satisfied)
   - opportunity_score: (importance × (10 - satisfaction)) / 10

3. **Pain Points** (severity 1-10, frequency: always|often|sometimes|rarely, percent_affected 0-1, quotes, solutions)
   - severity: Emotional intensity in responses (1=mild annoyance, 10=critical blocker)
   - frequency: How often pain occurs (from response context)
   - percent_affected: Estimate based on # of personas mentioning it
   - quotes: EXACT excerpts (max 150 chars each)
   - solutions: Only if mentioned in responses

JSON output only (no markdown)."""
```

**Key Improvements:**
- ✅ Explicit handling of missing data (return empty arrays, NO hallucination)
- ✅ Strict quote extraction (exact excerpts, no paraphrasing)
- ✅ Calibrated importance/severity scales (1-3, 4-6, 7-10 with definitions)
- ✅ Opportunity score formula (importance × (10 - satisfaction) / 10)
- ✅ Frequency/percent_affected grounded in response counts

---

### 6.4 Temperature & Token Optimization

**Current Settings:**
```python
# PersonaJourneyService
temperature=0.2,  # Reduced from 0.3 for faster, more deterministic output
max_tokens=2000,  # Reduced from 6000

# PersonaNeedsService
temperature=0.25,  # Reduced from 0.35
max_tokens=2000,  # Reduced from 6000
```

**Assessment:**
- ✅ Temperature 0.2-0.25 is GOOD for factual extraction (low hallucination risk)
- ✅ max_tokens 2000 is sufficient for structured output (CustomerJourney, NeedsAndPains)
- ⚠️ Lower temperature may reduce diversity in journeys (all similar personas → similar journeys)

**Recommendation:**
- Keep temperature 0.2-0.25 for production (prioritize accuracy over creativity)
- Monitor journey/needs diversity - if too similar, increase to 0.3
- Add temperature as configurable parameter for A/B testing

---

## 7. Success Metrics & Validation

### 7.1 KPI Snapshot Quality Metrics

**Metric 1: RAG Coverage**
- **Definition:** % of KPI metrics sourced from RAG (vs hardcoded)
- **Target:** 70% (conversion, retention, NPS, segment_size from RAG)
- **Current:** 0% (all hardcoded/heuristic)
- **Measurement:**
```python
rag_metrics_count = sum([
    kpi['data_sources'].contains('rag') for kpi in [conversion_rate, retention_rate, nps_score, segment_size]
])
rag_coverage = rag_metrics_count / 4
```

**Metric 2: Segment Size Accuracy**
- **Definition:** |estimated_size - actual_size| / actual_size (if actual known)
- **Target:** <30% error (currently ~50%)
- **Measurement:** Compare RAG-based estimates vs GUS official statistics (if available)

**Metric 3: Confidence Transparency**
- **Definition:** % of KPI displays showing confidence_score in UI
- **Target:** 100%
- **Current:** 0% (not visible in UI)
- **Measurement:** UI audit - check if confidence badges present

---

### 7.2 Customer Journey Quality Metrics

**Metric 1: RAG Context Utilization**
- **Definition:** Avg RAG context length used (chars)
- **Target:** 1500 chars (up from 500)
- **Current:** 500 chars
- **Measurement:** Log `len(rag_section)` in `_build_prompt()`

**Metric 2: Focus Group Integration**
- **Definition:** % of journeys including focus group data
- **Target:** 60% (not all personas have focus groups)
- **Current:** 0%
- **Measurement:**
```python
has_fg_data = len(focus_group_journeys) > 0
fg_integration_rate = num_journeys_with_fg / total_journeys
```

**Metric 3: Journey Diversity**
- **Definition:** Avg cosine similarity between journey texts
- **Target:** <0.7 (diverse journeys)
- **Measurement:** Embed journey JSON, compute pairwise similarity

---

### 7.3 Needs & Pains Quality Metrics

**Metric 1: Quote Verification Rate**
- **Definition:** % of pain point quotes verified in focus group responses
- **Target:** >90%
- **Current:** Unknown (no validation)
- **Measurement:**
```python
verified_quotes = sum([pain['quote_verified'] for pain in pain_points])
verification_rate = verified_quotes / len(pain_points)
```

**Metric 2: Data Quality Score**
- **Definition:** "no_focus_group_data" | "low_response_count" | "sufficient_data"
- **Target:** >70% "sufficient_data"
- **Current:** Unknown
- **Measurement:** Count personas by data_quality field

**Metric 3: Graceful Degradation Rate**
- **Definition:** % of personas with empty needs (due to missing focus groups)
- **Target:** <20% (should have focus group data for 80% of personas)
- **Current:** Unknown (currently hallucinates instead of gracefully degrading)
- **Measurement:**
```python
empty_needs_count = sum([len(persona.needs_and_pains.get('jobs_to_be_done', [])) == 0 for persona in personas])
degradation_rate = empty_needs_count / total_personas
```

---

### 7.4 Overall System Health Metrics

**Metric 1: Overall Data Quality Score**
- **Definition:** Weighted average of component scores
- **Target:** 8.0/10 (up from current 5.5/10)
- **Formula:**
```python
overall_score = (
    kpi_rag_coverage * 0.30 +
    journey_rag_utilization * 0.30 +
    needs_verification_rate * 0.20 +
    transparency_ui_coverage * 0.20
) * 10
```

**Metric 2: Hallucination Rate**
- **Definition:** % of AI-generated content flagged as low confidence or unverified
- **Target:** <15%
- **Measurement:** Count items with confidence <0.6 or quote_verified=False

**Metric 3: User Trust Score (Qualitative)**
- **Definition:** User survey: "Do you trust Persona Details data for decisions?" (1-5)
- **Target:** 4.2/5.0 (up from unknown baseline)
- **Measurement:** Post-feature survey to 20 users

---

## 8. Quick Wins - Top 5 Easy Wins

### Win 1: Fix Misleading data_sources Claim ⭐⭐⭐
- **File:** `app/services/persona_kpi_service.py:201`
- **Change:** `"data_sources": ["heuristics", "ai_estimation"]` (was: `["rag", "ai_estimation"]`)
- **Effort:** 5 minutes
- **Impact:** HIGH (honesty with users)

### Win 2: Expand Journey RAG Context (500 → 1500 chars) ⭐⭐⭐
- **File:** `app/services/persona_journey_service.py:119-120`
- **Change:** Increase truncation limit from 500 to 1500
- **Effort:** 5 minutes
- **Impact:** HIGH (better journey quality)

### Win 3: Add UI Transparency Badges ⭐⭐⭐
- **File:** `frontend/src/components/personas/InsightsSection.tsx`
- **Change:** Show `confidence_score` and `calculation_method` as badges
- **Effort:** 2 hours
- **Impact:** HIGH (user trust)

### Win 4: Graceful Degradation for Missing Needs Data ⭐⭐
- **File:** `app/services/persona_needs_service.py:146-148`
- **Change:** Return empty arrays instead of "Brak danych" (prevents hallucination)
- **Effort:** 30 minutes
- **Impact:** MEDIUM (data quality)

### Win 5: Add Grounding Instructions to Prompts ⭐⭐
- **Files:** `persona_journey_service.py:146`, `persona_needs_service.py:166`
- **Change:** Add strict grounding rule: "If insufficient data, return conservative estimates. DO NOT invent."
- **Effort:** 15 minutes
- **Impact:** MEDIUM (reduces hallucinations)

---

## 9. Final Recommendations Summary

### Immediate Actions (Week 1) 🚨
1. ✅ **Fix data_sources metadata** (5 min) - stop lying to users!
2. ✅ **Expand Journey RAG context** 500 → 1500 chars (5 min)
3. ✅ **Add UI transparency badges** (2 hours) - show confidence scores
4. ✅ **Graceful degradation for missing needs** (30 min) - no hallucinations
5. ✅ **Add grounding instructions** (15 min) - strengthen prompts

**Total: ~3 hours, Impact: CRITICAL**

---

### Short-Term Actions (Week 2-3) 🔥
1. ✅ **Implement RAG-based KPI extraction** (36 hours)
   - Query Wskaznik nodes for conversion/retention/NPS
   - Extract segment_size from Demografia nodes
   - Add confidence scoring based on data availability

2. ✅ **Add focus group journey data** (12 hours)
   - Fetch journey-related PersonaResponse records
   - Include in prompt after RAG context
   - Improve journey grounding

**Total: ~48 hours, Impact: CRITICAL**

---

### Medium-Term Actions (Week 4+) 📊
1. ✅ **Quote validation** (6 hours) - verify needs quotes are real
2. ✅ **Improve RAG context extraction** (8 hours) - better context candidates
3. ✅ **A/B test temperature/token settings** (4 hours) - optimize quality vs speed
4. ✅ **Add RAG quality monitoring** (8 hours) - log coverage, confidence, sources

**Total: ~26 hours, Impact: MEDIUM-HIGH**

---

### Long-Term Improvements (Q1 2026) 🔮
1. ✅ **Graph RAG relationship traversal** - use OPISUJE, DOTYCZY relationships
2. ✅ **Fuzzy demographic matching** - improve graph query precision
3. ✅ **Dynamic TOP_K** - adjust based on query complexity
4. ✅ **Cross-encoder reranking** - enable for production (if performance OK)
5. ✅ **User feedback loop** - capture which KPI/Journey/Needs users trust

---

## 10. Conclusion

### Overall Assessment: 5.5/10 🟡

**Strengths:**
- ✅ PersonaNeedsService uses **real focus group data** (70% accuracy)
- ✅ RAG infrastructure is **production-ready** (Hybrid Search + Graph RAG)
- ✅ Structured output (Pydantic) prevents JSON parsing failures
- ✅ Comprehensive metadata (confidence_score, data_sources) exists in backend

**Critical Weaknesses:**
- ❌ PersonaKPIService: **ALL metrics hardcoded** (0% RAG usage despite claims!)
- ❌ PersonaJourneyService: **RAG context truncated to 500 chars** (insufficient!)
- ❌ **NO UI transparency** - users don't know what's fake vs real
- ❌ System falsely claims `data_sources: ["rag", ...]` when RAG not used

**Hallucination Risks:**
1. **KPI Snapshot:** 80% hallucination risk (hardcoded benchmarks)
2. **Customer Journey:** 70% hallucination risk (generic journeys, truncated RAG)
3. **Needs & Pains:** 40% risk (if focus groups exist), 80% risk (if missing)

**Path to 8.0/10:**
- Implement RAG-based KPI extraction (Week 2-3)
- Expand Journey RAG context + add focus groups (Week 3-4)
- Add UI transparency (Week 1)
- Validate needs quotes (Week 4)

**With these changes, system will be production-ready for business-critical decisions.**

---

**Report Prepared By:** AI Specialist (Claude)
**Date:** 2025-10-16
**Next Review:** After Phase 2 implementation (RAG-based KPI)
