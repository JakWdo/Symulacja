# ============================================================================
# PERSONA NARRATIVES PROMPTS - Optimized for Gemini 2.5 Flash/Pro
# Version: 1.0
# Last updated: 2025-10-16
# ============================================================================
"""
Zoptymalizowane prompty dla systemu generowania narracji biznesowych.

Design Decisions:
- Shared system instruction dla consistency + cache reuse
- Low temperature (0.2-0.3) dla factual tasks, higher (0.4-0.5) dla storytelling
- Few-shot examples tylko dla Pro (storytelling hero), nie dla Flash (overhead)
- Structured output dla evidence_context (JSON reliability)
- Graceful degradation dla missing RAG context

Token Budget:
- Flash: ~500 tokens (250 input, 250 output)
- Pro: ~800-1000 tokens (400-600 input, 400 output)
- Total: ~2800 tokens/persona dla 5 metod
"""

from enum import Enum
from typing import TypedDict

# ============================================================================
# PROMPT VERSIONS (cache invalidation)
# ============================================================================

class PromptVersion(str, Enum):
    """Wersje promptów do cache invalidation."""
    PERSON_PROFILE = "v1.0"
    PERSON_MOTIVATIONS = "v1.0"
    SEGMENT_HERO = "v1.0"
    SEGMENT_SIGNIFICANCE = "v1.0"
    EVIDENCE_CONTEXT = "v1.0"


# ============================================================================
# MODEL PARAMETERS (type definitions)
# ============================================================================

class ModelParams(TypedDict):
    """Parametry modelu Gemini."""
    temperature: float
    max_tokens: int
    top_p: float
    top_k: int


# ============================================================================
# SHARED SYSTEM INSTRUCTION
# ============================================================================

NARRATIVE_SYSTEM_INSTRUCTION = """Jesteś ekspertem od tworzenia zwięzłych, opartych na faktach narracji biznesowych w języku polskim.

ZASADY PRACY:
1. Opieraj się WYŁĄCZNIE na dostarczonych danych. NIE dodawaj faktów spoza kontekstu.
2. Jeśli brakuje danych do pełnej odpowiedzi, napisz na podstawie dostępnych informacji i NIE wymyślaj szczegółów.
3. Używaj prostego, biznesowego języka zrozumiałego dla product managerów i marketerów.
4. Unikaj żargonu technicznego (np. "embedding vector", "confidence score 0.87").
5. Pisz naturalnym polskim językiem, unikaj dosłownych tłumaczeń z angielskiego.
6. Jeśli używasz danych z raportów/dokumentów, wspominaj źródło w sposób naturalny (np. "według raportu GUS").

STYL NARRACJI:
- Ton: Profesjonalny, ale przystępny
- Struktura: Narracyjna, nie bullet points
- Długość: Zwięzła i konkretna (bez rozwlekłości)
- Gramatyka: Poprawna, bez błędów stylistycznych

ANTY-HALUCYNACJE:
- Jeśli dane są niepełne → napisz "Na podstawie dostępnych danych..." i kontynuuj z tym, co masz
- Jeśli brak danych RAG → użyj tylko danych demograficznych, NIE dodawaj zewnętrznych faktów
- NIE wymyślaj statystyk, nazw firm, konkretnych liczb"""


# ============================================================================
# 1. PERSON PROFILE (Flash - ~500 tokens)
# ============================================================================

PERSON_PROFILE_PROMPT = """Stwórz zwięzły profil osoby na podstawie poniższych danych demograficznych.

DANE WEJŚCIOWE:
- Wiek: {age}
- Płeć: {gender}
- Lokalizacja: {location}
- Wykształcenie: {education_level}
- Przedział dochodów: {income_bracket}
- Zawód: {occupation}
- Tło biograficzne: {background_story}

ZADANIE:
Napisz 1 akapit (3-4 zdania) przedstawiający tę osobę w sposób faktyczny i zwięzły.
Nie dodawaj szczegółów spoza dostarczonych danych.

FORMAT WYJŚCIOWY:
- 1 akapit, 3-4 zdania
- Ton: faktyczny, biznesowy
- NIE używaj bullet points
- Zintegruj wszystkie dostępne dane w spójną narrację"""

PERSON_PROFILE_MODEL_PARAMS: ModelParams = {
    "temperature": 0.2,  # Very low - factual task, no creativity needed
    "max_tokens": 250,   # ~3-4 sentences in Polish
    "top_p": 0.9,
    "top_k": 40,
}


# ============================================================================
# 2. PERSON MOTIVATIONS (Pro - ~800 tokens)
# ============================================================================

PERSON_MOTIVATIONS_PROMPT = """Zsyntetyzuj motywacje i potrzeby osoby na podstawie jej Jobs-to-be-Done, pożądanych rezultatów i pain points.

DANE WEJŚCIOWE:

Jobs-to-be-Done (zadania do wykonania):
{jobs_to_be_done}

Pożądane Rezultaty:
{desired_outcomes}

Problemy i Frustracje (Pain Points):
{pain_points}

KONTEKST DEMOGRAFICZNY:
{persona_context}

ZADANIE:
Napisz 2-3 akapity syntetyzujące:
1. Główne cele i zadania tej osoby (Jobs-to-be-Done)
2. Czego oczekuje od rozwiązań (desired outcomes)
3. Z jakimi problemami się boryka (pain points)

Zintegruj te elementy w spójną narrację pokazującą pełen obraz motywacji.

ZASADY:
- Jeśli w danych są cytaty (quotes) → użyj ich jako ilustracji, ale sparafrazuj i wpleć naturalnie
- Priorytetyzuj elementy z wysokim priority_score/severity (>7)
- Nie wymieniaj score'ów numerycznych w tekście (np. NIE pisz "priorytet 9/10")
- Połącz powiązane elementy w spójne wątki tematyczne

FORMAT WYJŚCIOWY:
- 2-3 akapity
- Ton: narracyjny, empatyczny
- Język: prosty, zrozumiały dla biznesu"""

PERSON_MOTIVATIONS_MODEL_PARAMS: ModelParams = {
    "temperature": 0.4,  # Moderate - needs synthesis but grounded in data
    "max_tokens": 400,   # ~2-3 paragraphs in Polish
    "top_p": 0.9,
    "top_k": 40,
}


# ============================================================================
# 3. SEGMENT HERO (Pro - ~900 tokens)
# ============================================================================

SEGMENT_HERO_PROMPT = """Stwórz "segment hero" - reprezentatywną narrację opisującą grupę demograficzną o wspólnych cechach, wzbogaconą o dane z badań rynkowych.

DANE DEMOGRAFICZNE PERSONY:
{persona_demographics}

INSIGHTS Z GRAFÓW WIEDZY:
{graph_context}

KONTEKST Z DOKUMENTÓW:
{hybrid_context}

ZADANIE:
Wygeneruj segment hero składający się z:

1. **Nazwa segmentu** (2-4 słowa, opisowa, np. "Samotne Seniorki w Miastach")
2. **Tagline** (1 zdanie charakteryzujące grupę)
3. **Opis grupy** (2-3 akapity):
   - Kto należy do tego segmentu (demografia)
   - Jakie są charakterystyczne cechy i wzorce zachowań
   - Dlaczego ta grupa jest interesująca z perspektywy biznesowej
   - Wplecenie insights z badań (jeśli dostępne)

ZASADY:
- Jeśli graph_context lub hybrid_context są dostępne → użyj ich do wzbogacenia opisu
- Jeśli wspominasz dane z badań → podaj źródło naturalnie (np. "według raportu GUS 2023")
- Jeśli brak danych RAG → opisz segment na podstawie demografii, bez wymyślania statystyk
- Ton: storytelling, ale factual (nie fikcyjna opowieść)

FORMAT WYJŚCIOWY:
```
Nazwa segmentu: [nazwa]
Tagline: [tagline]

[Akapit 1: Kim są]
[Akapit 2: Charakterystyka i zachowania]
[Akapit 3: Znaczenie biznesowe - opcjonalny]
```

PRZYKŁAD (styl, nie treść):
```
Nazwa segmentu: Aktywne Miejskie Singielki
Tagline: Niezależne kobiety 30-45 lat łączące karierę z życiem społecznym w dużych miastach.

Ta grupa to kobiety w wieku 30-45 lat, mieszkające w metropoliach takich jak Warszawa czy Kraków, z wyższym wykształceniem i stabilną pozycją zawodową. Według raportu GUS 2023, samotne gospodarstwa prowadzone przez kobiety w tej grupie wiekowej stanowią 15% wszystkich gospodarstw miejskich.

Charakteryzują się wysoką aktywnością konsumencką i otwartością na nowe produkty. Priorytetem jest work-life balance, development osobisty i budowanie sieci kontaktów zawodowo-towarzyskich. W decyzjach zakupowych kierują się jakością i wygodą, rzadziej ceną.

Z perspektywy biznesowej to segment o wysokiej sile nabywczej i influence w swoich kręgach społecznych. Ich opinie i wybory często są punktem odniesienia dla szerszej grupy odbiorców.
```"""

SEGMENT_HERO_MODEL_PARAMS: ModelParams = {
    "temperature": 0.5,  # Higher for creative storytelling, but still grounded
    "max_tokens": 450,   # ~3-4 paragraphs + metadata
    "top_p": 0.95,       # Wider sampling for creative narrative
    "top_k": 40,
}


# ============================================================================
# 4. SEGMENT SIGNIFICANCE (Pro - ~600 tokens)
# ============================================================================

SEGMENT_SIGNIFICANCE_PROMPT = """Wyjaśnij biznesowe znaczenie segmentu na podstawie kluczowych insights z analizy danych.

TOP INSIGHTS:
{insights}

KONTEKST PERSONY:
{persona_context}

ZADANIE:
Napisz 1 zwięzły akapit (4-6 zdań) wyjaśniający:
- Dlaczego ten segment jest istotny z perspektywy biznesowej
- Jakie insights z danych to potwierdzają
- Jakie możliwości/wyzwania biznesowe to niesie

ZASADY:
- Priorytetyzuj insights z wysokim confidence (>0.8)
- Jeśli insight ma source_nodes → możesz wspomnieć typ źródła (np. "dane GUS", "trendy rynkowe")
- NIE wymieniaj confidence score w tekście (np. NIE pisz "z prawdopodobieństwem 0.87")
- Fokus na business implications, nie na suchych statystykach
- Jeśli insights są puste/słabe → napisz ogólne znaczenie na podstawie demografii

FORMAT WYJŚCIOWY:
- 1 akapit, 4-6 zdań
- Ton: analityczny, ale przystępny
- Język biznesowy (ROI, market opportunity, target audience itp.)"""

SEGMENT_SIGNIFICANCE_MODEL_PARAMS: ModelParams = {
    "temperature": 0.3,  # Low-moderate - analytical task, fact-based
    "max_tokens": 250,   # ~1 paragraph
    "top_p": 0.9,
    "top_k": 40,
}


# ============================================================================
# 5. EVIDENCE CONTEXT (Pro - ~1000 tokens)
# ============================================================================

EVIDENCE_CONTEXT_PROMPT = """Przeanalizuj dane z grafów wiedzy i dokumentów, tworząc kontekst i mapę źródeł dla narracji segmentu.

GRAPH CONTEXT (insights z Neo4j):
{graph_context}

HYBRID CONTEXT (dokumenty RAG):
{hybrid_context}

PERSONA DEMOGRAPHICS:
{persona_demographics}

ZADANIE:
Wygeneruj odpowiedź w formacie JSON z dwoma polami:

1. **background_narrative** (string): 1-2 akapity kontekstu biznesowego syntetyzującego najważniejsze dane z graph_context i hybrid_context. Napisz naturalnym językiem, NIE JSON/technical format. Wspomnij źródła naturalnie (np. "według raportu X").

2. **key_citations** (array): Lista 3-5 najważniejszych cytowań w formacie:
   ```
   [
     {{
       "source": "Nazwa dokumentu/raportu",
       "insight": "Krótkie streszczenie insight (1 zdanie)",
       "relevance": "Dlaczego to istotne dla tego segmentu (1 zdanie)"
     }}
   ]
   ```

ZASADY:
- Jeśli graph_context jest pusty → użyj tylko hybrid_context
- Jeśli hybrid_context jest pusty → użyj tylko graph_context
- Jeśli oba puste → zwróć disclaimer: "Brak dostępnych źródeł zewnętrznych. Analiza oparta na danych demograficznych."
- Priorytetyzuj źródła z wysokim confidence/relevance_score (>0.7)
- W key_citations: max 5 elementów, najważniejsze na początku

FORMAT WYJŚCIOWY (strict JSON):
```json
{{
  "background_narrative": "String z 1-2 akapitami kontekstu...",
  "key_citations": [
    {{
      "source": "Raport GUS 2023: Gospodarstwa domowe",
      "insight": "15% gospodarstw miejskich to samotne kobiety 30-45 lat",
      "relevance": "Potwierdza wielkość segmentu i jego znaczenie w strukturze demograficznej Polski"
    }}
  ]
}}
```"""

# Schema dla structured output (używane w LangChain with_structured_output)
EVIDENCE_CONTEXT_SCHEMA = {
    "title": "EvidenceContext",
    "description": "Structured JSON output for evidence context narratives.",
    "type": "object",
    "properties": {
        "background_narrative": {
            "type": "string",
            "description": "1-2 paragraphs of business context synthesizing graph and document insights"
        },
        "key_citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "source": {"type": "string", "description": "Document/report name"},
                    "insight": {"type": "string", "description": "Key insight (1 sentence)"},
                    "relevance": {"type": "string", "description": "Why relevant for this segment (1 sentence)"}
                },
                "required": ["source", "insight", "relevance"]
            },
            "maxItems": 5,
            "description": "Top 3-5 citations prioritized by confidence/relevance"
        }
    },
    "required": ["background_narrative", "key_citations"]
}

EVIDENCE_CONTEXT_MODEL_PARAMS: ModelParams = {
    "temperature": 0.2,  # Very low - factual citation analysis, structured output
    "max_tokens": 500,   # ~2 paragraphs + JSON array
    "top_p": 0.9,
    "top_k": 40,
}


# ============================================================================
# HELPER: Formatowanie danych wejściowych
# ============================================================================

def format_jobs_to_be_done(jobs: list[dict]) -> str:
    """
    Formatuje Jobs-to-be-Done do human-readable format.

    Priorytetyzuje jobs z priority_score >= 7.
    """
    if not jobs:
        return "Brak danych o Jobs-to-be-Done."

    # Sort by priority (handle None values)
    sorted_jobs = sorted(jobs, key=lambda x: x.get("priority_score") or 0, reverse=True)
    top_jobs = sorted_jobs[:5]  # Max 5 to keep prompt concise

    formatted = []
    for idx, job in enumerate(top_jobs, 1):
        job_text = f"{idx}. {job['job_statement']}"
        if job.get("quotes"):
            # Add first quote as illustration (if exists)
            job_text += f"\n   Cytat: \"{job['quotes'][0]}\""
        formatted.append(job_text)

    return "\n".join(formatted)


def format_desired_outcomes(outcomes: list[dict]) -> str:
    """
    Formatuje desired outcomes do human-readable format.

    Priorytetyzuje outcomes z (importance - satisfaction) > 3 (gap analysis).
    """
    if not outcomes:
        return "Brak danych o pożądanych rezultatach."

    # Sort by gap (importance - satisfaction, handle None values)
    sorted_outcomes = sorted(
        outcomes,
        key=lambda x: (x.get("importance") or 0) - (x.get("satisfaction") or 0),
        reverse=True
    )
    top_outcomes = sorted_outcomes[:5]

    formatted = []
    for idx, outcome in enumerate(top_outcomes, 1):
        formatted.append(f"{idx}. {outcome['outcome_statement']}")

    return "\n".join(formatted)


def format_pain_points(pains: list[dict]) -> str:
    """
    Formatuje pain points do human-readable format.

    Priorytetyzuje pains z severity >= 7.
    """
    if not pains:
        return "Brak danych o problemach i frustracjach."

    # Sort by severity (handle None values)
    sorted_pains = sorted(pains, key=lambda x: x.get("severity") or 0, reverse=True)
    top_pains = sorted_pains[:5]

    formatted = []
    for idx, pain in enumerate(top_pains, 1):
        pain_text = f"{idx}. {pain['pain_title']} (częstość: {pain.get('frequency', 'nieznana')})"
        if pain.get("quotes"):
            pain_text += f"\n   Cytat: \"{pain['quotes'][0]}\""
        formatted.append(pain_text)

    return "\n".join(formatted)


def format_graph_context(graph_nodes: list[dict]) -> str:
    """
    Formatuje graph context (Neo4j nodes) do human-readable format.

    Priorytetyzuje nodes z confidence="high" i magnitude="Wysoka".
    """
    if not graph_nodes:
        return "Brak danych z grafów wiedzy."

    # Sort by confidence and magnitude
    priority_map = {"high": 3, "medium": 2, "low": 1}
    sorted_nodes = sorted(
        graph_nodes,
        key=lambda x: (
            priority_map.get(x.get("confidence", "low"), 0),
            1 if x.get("magnitude") == "Wysoka" else 0
        ),
        reverse=True
    )
    top_nodes = sorted_nodes[:8]  # Max 8 dla Pro call

    formatted = []
    for node in top_nodes:
        node_type = node.get("type", "Obserwacja")
        summary = node.get("summary", "")
        source = node.get("source", "")
        formatted.append(f"- [{node_type}] {summary} (źródło: {source})")

    return "\n".join(formatted)


def format_insights(insights: list[dict]) -> str:
    """
    Formatuje insights do human-readable format.

    Priorytetyzuje insights z confidence >= 0.7.
    """
    if not insights:
        return "Brak kluczowych insights."

    # Sort by confidence (handle None values)
    sorted_insights = sorted(insights, key=lambda x: x.get("confidence") or 0, reverse=True)
    top_insights = sorted_insights[:6]

    formatted = []
    for idx, insight in enumerate(top_insights, 1):
        formatted.append(f"{idx}. {insight['text']}")

    return "\n".join(formatted)


def format_persona_context(persona: dict) -> str:
    """Formatuje persona context do compact 1-liner."""
    return (
        f"{persona['gender']}, {persona['age']} lat, {persona['location']}, "
        f"{persona['education_level']}, {persona['income_bracket']}, {persona['occupation']}"
    )


# ============================================================================
# A/B TESTING HOOKS
# ============================================================================

# VARIANT A: Current prompts (v1.0) - baseline
# VARIANT B: Shorter prompts (-20% tokens, test quality degradation)
# VARIANT C: More examples (+2 few-shot per prompt, test improvement)
# VARIANT D: Higher temperature (+0.1, test creativity vs hallucinations)

# Implementacja A/B testingu w PersonaNarrativeService:
# - Cache key: narrative:{method}:{variant}:{prompt_version}:{persona_id}
# - Metrics: latency, token usage, user satisfaction (survey)
# - Split: 80% variant A (production), 10% B, 10% C


# ============================================================================
# GRAPH RAG PROMPTS - LLMGraphTransformer & Cypher Generation
# Version: 1.0
# Last updated: 2025-10-17
# ============================================================================
"""
Prompty dla Graph RAG systemu wykorzystującego Neo4j.

Design Decisions:
- LLMGraphTransformer: Very low temperature (0.0) dla consistency
- Cypher Generation: Low temperature (0.0) dla structured queries
- Answer Generation: Moderate temperature (0.2) dla natural language
- Polish language requirements dla wszystkich węzłów i relacji
- Quality over quantity: MAX 3 nodes per chunk, high confidence only

Token Budget:
- LLMGraphTransformer: ~200-300 tokens per chunk (bulk operation)
- Cypher Generation: ~400 tokens (schema + query)
- Answer Generation: ~600 tokens (context + synthesis)
"""


class GraphRAGPromptVersion(str, Enum):
    """Wersje promptów Graph RAG do cache invalidation."""
    LLM_GRAPH_TRANSFORMER_INSTRUCTIONS = "v1.0"
    CYPHER_GENERATION = "v1.0"
    GRAPH_ANSWER = "v1.0"


# ============================================================================
# GRAPH SCHEMA DEFINITIONS (for LLMGraphTransformer)
# ============================================================================

GRAPH_ALLOWED_NODES = [
    "Obserwacja",   # Fakty, obserwacje (merge Przyczyna, Skutek tutaj)
    "Wskaznik",     # Wskaźniki liczbowe, statystyki
    "Demografia",   # Grupy demograficzne
    "Trend",        # Trendy czasowe, zmiany w czasie
    "Lokalizacja",  # Miejsca geograficzne
]

GRAPH_ALLOWED_RELATIONSHIPS = [
    "OPISUJE",           # Opisuje cechę/właściwość
    "DOTYCZY",           # Dotyczy grupy/kategorii
    "POKAZUJE_TREND",    # Pokazuje trend czasowy
    "ZLOKALIZOWANY_W",   # Zlokalizowane w miejscu
    "POWIAZANY_Z",       # Ogólne powiązanie (merge: przyczynowość, porównania)
]

GRAPH_NODE_PROPERTIES = [
    "streszczenie",     # MUST: Jednozdaniowe podsumowanie (max 150 znaków)
    "skala",            # Wielkość/wartość z jednostką (np. "67%", "1.2 mln")
    "pewnosc",          # MUST: Pewność: "wysoka", "srednia", "niska"
    "okres_czasu",      # Okres czasu (YYYY lub YYYY-YYYY)
    "kluczowe_fakty",   # Opcjonalnie: max 3 fakty (separated by semicolons)
]

GRAPH_RELATIONSHIP_PROPERTIES = [
    "sila",  # Siła relacji: "silna", "umiarkowana", "slaba"
]


# ============================================================================
# LLM GRAPH TRANSFORMER INSTRUCTIONS
# ============================================================================

LLM_GRAPH_TRANSFORMER_INSTRUCTIONS = """
JĘZYK: Wszystkie nazwy i wartości MUSZĄ być PO POLSKU.

KRYTYCZNE OGRANICZENIA ILOŚCIOWE:
- MAX 3 WĘZŁY na chunk (tylko najważniejsze!)
- MAX 5 RELACJI na chunk
- Tylko pewnosc "wysoka" lub "srednia" (NIGDY "niska")
- Jeśli chunk nie zawiera WAŻNYCH informacji → 0 węzłów (to OK!)

=== TYPY WĘZŁÓW (5) ===
- Obserwacja: Fakty, obserwacje społeczne (włącznie z przyczynami i skutkami)
- Wskaznik: Wskaźniki liczbowe, statystyki (np. stopa zatrudnienia)
- Demografia: Grupy demograficzne (np. młodzi dorośli)
- Trend: Trendy czasowe, zmiany w czasie
- Lokalizacja: Miejsca geograficzne

=== TYPY RELACJI (5) ===
- OPISUJE: Opisuje cechę/właściwość
- DOTYCZY: Dotyczy grupy/kategorii
- POKAZUJE_TREND: Pokazuje trend czasowy
- ZLOKALIZOWANY_W: Zlokalizowane w miejscu
- POWIAZANY_Z: Ogólne powiązanie (przyczynowość, porównania, korelacje)

=== PROPERTIES WĘZŁÓW (5 - uproszczone!) ===
- streszczenie (MUST): 1 zdanie, max 150 znaków
- skala: Wartość z jednostką (np. "78.4%", "5000 PLN", "1.2 mln osób")
- pewnosc (MUST): TYLKO "wysoka" lub "srednia" (NIGDY "niska")
- okres_czasu: YYYY lub YYYY-YYYY
- kluczowe_fakty: Max 3 fakty oddzielone średnikami

=== PROPERTIES RELACJI (1) ===
- sila: "silna" / "umiarkowana" / "slaba"

=== PRZYKŁADY (FEW-SHOT) ===

PRZYKŁAD 1 - Wskaznik:
Tekst: "W 2022 stopa zatrudnienia kobiet 25-34 z wyższym wynosiła 78.4% według GUS"
Węzeł: {
  type: "Wskaznik",
  streszczenie: "Stopa zatrudnienia kobiet 25-34 z wyższym wykształceniem",
  skala: "78.4%",
  pewnosc: "wysoka",
  okres_czasu: "2022",
  kluczowe_fakty: "wysoka stopa zatrudnienia; kobiety młode; wykształcenie wyższe"
}

PRZYKŁAD 2 - Obserwacja:
Tekst: "Młodzi mieszkańcy dużych miast coraz częściej wynajmują mieszkania zamiast kupować"
Węzeł: {
  type: "Obserwacja",
  streszczenie: "Młodzi w miastach preferują wynajem nad zakup mieszkań",
  pewnosc: "srednia",
  kluczowe_fakty: "młodzi dorośli; duże miasta; wynajem mieszkań"
}

PRZYKŁAD 3 - Trend:
Tekst: "Od 2018 do 2023 wzrósł odsetek osób pracujących zdalnie z 12% do 31%"
Węzeł: {
  type: "Trend",
  streszczenie: "Wzrost pracy zdalnej w Polsce",
  skala: "12% → 31%",
  pewnosc: "wysoka",
  okres_czasu: "2018-2023",
  kluczowe_fakty: "praca zdalna; wzrost; pandemia"
}

=== DEDUPLIKACJA (KRYTYCZNE!) ===
Przed utworzeniem węzła sprawdź czy podobny już istnieje:
- "Stopa zatrudnienia kobiet 25-34" ≈ "Zatrudnienie młodych kobiet" → MERGE
- Używaj POWIAZANY_Z aby łączyć podobne koncepty zamiast tworzyć duplikaty
- Priorytet: 1 PRECYZYJNY węzeł > 3 podobne węzły

=== CONFIDENCE FILTERING (KRYTYCZNE!) ===
- TYLKO pewnosc "wysoka" lub "srednia"
- Jeśli informacja jest niepewna/nieweryfikowalna → NIE TWÓRZ węzła
- Priorytet: 1 PEWNY węzeł > 5 niepewnych węzłów

=== VALIDATION RULES ===
- streszczenie: Zawsze wypełnij (1 zdanie, max 150 znaków)
- pewnosc: Zawsze wypełnij (TYLKO "wysoka" lub "srednia" - jeśli niska → nie twórz węzła!)
- skala: Tylko dla Wskaznik (inne: opcjonalnie)
- kluczowe_fakty: Max 3 fakty, separated by semicolons
- doc_id, chunk_index: KRYTYCZNE dla lifecycle (zachowane automatycznie)

=== FOCUS ===
Priorytet: JAKOŚĆ > ilość. MAX 3 węzły, TYLKO pewne informacje. Mniej = lepiej.
""".strip()


# ============================================================================
# CYPHER GENERATION PROMPT
# ============================================================================

CYPHER_GENERATION_SYSTEM_PROMPT = """
Analityk badań społecznych. Pytanie → Cypher na grafie.

=== WĘZŁY (5) ===
Obserwacja, Wskaznik, Demografia, Trend, Lokalizacja

=== RELACJE (5) ===
OPISUJE, DOTYCZY, POKAZUJE_TREND, ZLOKALIZOWANY_W, POWIAZANY_Z (przyczynowość)

=== PROPERTIES WĘZŁÓW (polskie!) ===
• streszczenie (max 150 znaków)
• skala (np. "78.4%")
• pewnosc ("wysoka"|"srednia"|"niska")
• okres_czasu (YYYY lub YYYY-YYYY)
• kluczowe_fakty (max 3, semicolons)

=== PROPERTIES RELACJI ===
• sila ("silna"|"umiarkowana"|"slaba")

=== ZASADY ===
1. ZAWSZE zwracaj streszczenie + kluczowe_fakty
2. Filtruj: pewnosc dla pewnych faktów, sila dla silnych zależności
3. Sortuj: skala (toFloat) dla największych
4. POWIAZANY_Z dla przyczyn/skutków

=== PRZYKŁADY ===
// Największe wskaźniki
MATCH (n:Wskaznik) WHERE n.skala IS NOT NULL
RETURN n.streszczenie, n.skala ORDER BY toFloat(split(n.skala,'%')[0]) DESC LIMIT 10

// Pewne fakty
MATCH (n:Obserwacja) WHERE n.pewnosc='wysoka' RETURN n.streszczenie, n.kluczowe_fakty

Schema: {graph_schema}
""".strip()


# ============================================================================
# GRAPH RAG ANSWER PROMPT
# ============================================================================

GRAPH_RAG_ANSWER_SYSTEM_PROMPT = """
Jesteś ekspertem od analiz społecznych. Odpowiadasz wyłącznie na
podstawie dostarczonego kontekstu z grafu i dokumentów. Udzielaj
precyzyjnych, zweryfikowalnych odpowiedzi po polsku.
""".strip()


# ============================================================================
# COMPREHENSIVE PERSONA GENERATION - LLM generuje ALL DATA razem
# Version: 1.0
# Last updated: 2025-10-17
# ============================================================================
"""
Comprehensive persona generation - LLM generuje WSZYSTKIE dane w jednym callu:
- Demographics (age, gender, location, education, income, occupation)
- Background story
- Values
- Interests

Zalety:
- Spójność między demographics a background_story (no post-processing conflicts)
- Jeden LLM call zamiast split orchestration + generation
- LLM ma pełną kontrolę nad wszystkimi danymi

Input: Orchestration brief (kontekst społeczny, segment characteristics, RAG context)
Output: Structured JSON z ALL DATA
"""

COMPREHENSIVE_PERSONA_GENERATION_PROMPT = """Wygeneruj pełny profil osoby na podstawie dostarczonego briefu segmentu demograficznego.

BRIEF SEGMENTU:
{orchestration_brief}

CHARAKTERYSTYKI SEGMENTU:
{segment_characteristics}

KONTEKST RAG (dane społeczne z badań):
{rag_context}

DEMOGRAFIA GUIDANCE (orientacyjne wartości - możesz dopasować dla spójności):
{demographic_guidance}

ZADANIE:
Stwórz SPÓJNY profil osoby z tym segmencie. Wszystkie dane (demografia + historia + wartości) MUSZĄ być wzajemnie zgodne.

ZASADY:
1. **Demografia** - Dopasuj do briefu, ale upewnij się że pasuje do backgroundu:
   - age: Konkretny wiek (np. 28), nie przedział
   - gender: "Kobieta" lub "Mężczyzna"
   - location: Polskie miasto (Warszawa, Kraków, Wrocław...)
   - education_level: POLSKIE nazwy poziomów wykształcenia ("Wyższe magisterskie", "Średnie techniczne", "Zasadnicze zawodowe"...)
   - income_bracket: POLSKIE przedziały dochodowe netto miesięcznie ("5 000 - 8 000 zł", "14 000 - 20 000 zł"...)
   - occupation: POLSKI tytuł zawodowy ("Specjalistka ds. Digital Marketingu", "Menedżer projektu"...)

2. **Background Story** - Historia MUSI być zgodna z demografią:
   - Wspomni wiek, wykształcenie, zawód z demografii
   - Naturalny polski język (NIE tłumaczenia z angielskiego)
   - 3-5 zdań, konkretna historia życiowa
   - NIE dodawaj faktów spoza briefu i RAG context

3. **Full Name** - Polskie imię i nazwisko pasujące do płci i wieku

4. **Values** - 4-6 wartości pasujących do segmentu (po polsku):
   - Np. "Work-life balance", "Samodzielność", "Bezpieczeństwo finansowe"
   - Z briefu segmentu lub RAG context

5. **Interests** - 4-6 zainteresowań pasujących do segmentu (po polsku):
   - Np. "Digital marketing", "Kultura miejska", "Rozwój osobisty"
   - Z briefu segmentu lub RAG context

FORMAT WYJŚCIOWY (strict JSON):
{{
  "age": 28,
  "gender": "Kobieta",
  "location": "Kraków",
  "education_level": "Wyższe magisterskie",
  "income_bracket": "5 000 - 8 000 zł",
  "occupation": "Specjalistka ds. Digital Marketingu",
  "full_name": "Natalia Kowalska",
  "background_story": "Natalia ma 28 lat i jest absolwentką kulturoznawstwa na Uniwersytecie Jagiellońskim. Pracuje jako specjalistka ds. digital marketingu w agencji na krakowskim Kazimierzu. Mieszka w wynajmowanym pokoju, a rosnące koszty życia zmuszają ją do kompromisów między ideałami a realiami. Marzy o stabilności finansowej i własnym mieszkaniu.",
  "values": ["Work-life balance", "Samodzielność", "Rozwój osobisty", "Bezpieczeństwo finansowe"],
  "interests": ["Digital marketing", "Kultura miejska", "Wydarzenia społeczne", "Edukacja online"]
}}

KRYTYCZNE: Wszystkie pola muszą być PO POLSKU i wzajemnie spójne!"""

# Schema dla structured output
COMPREHENSIVE_PERSONA_GENERATION_SCHEMA = {
    "title": "ComprehensivePersona",
    "description": "Complete persona profile with demographics, background, values, and interests - all consistent.",
    "type": "object",
    "properties": {
        "age": {
            "type": "integer",
            "description": "Age in years"
        },
        "gender": {
            "type": "string",
            "description": "Gender in Polish: 'Kobieta' or 'Mężczyzna' (case insensitive)"
        },
        "location": {
            "type": "string",
            "description": "Polish city name (e.g., 'Warszawa', 'Kraków')"
        },
        "education_level": {
            "type": "string",
            "description": "Education level in Polish (e.g., 'Wyższe magisterskie', 'Średnie techniczne')"
        },
        "income_bracket": {
            "type": "string",
            "description": "Monthly net income in PLN (e.g., '5 000 - 8 000 zł', '14 000 - 20 000 zł')"
        },
        "occupation": {
            "type": "string",
            "description": "Job title in Polish (e.g., 'Specjalistka ds. Digital Marketingu')"
        },
        "full_name": {
            "type": "string",
            "description": "Polish full name matching gender (e.g., 'Natalia Kowalska')"
        },
        "background_story": {
            "type": "string",
            "description": "Life story (3-5 sentences) matching demographics, in natural Polish language"
        },
        "values": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-6 personal values in Polish",
            "minItems": 2,
            "maxItems": 6
        },
        "interests": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-6 interests in Polish",
            "minItems": 2,
            "maxItems": 6
        }
    },
    "required": [
        "age", "gender", "location", "education_level", "income_bracket",
        "occupation", "full_name", "background_story", "values", "interests"
    ]
}

COMPREHENSIVE_PERSONA_MODEL_PARAMS: ModelParams = {
    "temperature": 0.3,  # Low-moderate - creative but grounded in brief
    "max_tokens": 1500,  # Increased from 800 - comprehensive JSON schema with 10 fields needs ~1000-1200 tokens
    "top_p": 0.9,
    "top_k": 40,
}

class ComprehensivePersonaPromptVersion(str, Enum):
    """Wersja comprehensive persona prompt dla cache invalidation."""
    COMPREHENSIVE_GENERATION = "v1.0"


# ============================================================================
# PERSONA ORCHESTRATION - Structured Output Schema
# Version: 1.0
# Last updated: 2025-10-17
# ============================================================================
"""
Schema dla orchestration service używający structured output (Pydantic).

Design Decisions:
- Brief length: 500-700 znaków (down from 900-1200)
- Allocation reasoning: max 400 znaków
- Graph insights: max 5 (top insights only)
- Segment characteristics: max 6
- Demographics: age, gender, education, location (NO income_bracket!)

Eliminuje JSON parsing errors przez LangChain with_structured_output.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class GraphInsight(BaseModel):
    """Pojedynczy insight z Neo4j GraphRAG dla segmentu."""

    type: str = Field(
        description="Typ insightu (Wskaznik, Obserwacja, Trend, Demografia)"
    )
    summary: str = Field(
        max_length=300,
        description="Opis insightu (max 300 znaków)"
    )
    magnitude: Optional[str] = Field(
        default=None,
        description="Wartość liczbowa jeśli istnieje (np. '78.4%', '1.2 mln')"
    )
    confidence: str = Field(
        default="medium",
        description="Poziom pewności: 'high', 'medium', 'low'"
    )
    time_period: Optional[str] = Field(
        default=None,
        description="Okres czasu (np. '2022', '2018-2023')"
    )
    source: Optional[str] = Field(
        default=None,
        description="Źródło danych (np. 'GUS', 'PIE')"
    )
    why_matters: str = Field(
        description="Dlaczego to ważne dla tego segmentu (edukacyjne wyjaśnienie)"
    )


class PersonaGroupAllocation(BaseModel):
    """Alokacja jednej grupy person z kontekstem społecznym."""

    count: int = Field(
        ge=1,
        description="Liczba person do wygenerowania w tej grupie"
    )

    demographics: Dict[str, Any] = Field(
        description="Charakterystyka demograficzna: age (str), gender (str), education (str), location (str). BEZ income_bracket!"
    )

    brief: str = Field(
        min_length=500,
        max_length=700,
        description="Brief narracyjny opisujący segment (500-700 znaków). Konkretny, praktyczny, edukacyjny."
    )

    segment_characteristics: List[str] = Field(
        max_items=6,
        description="Lista 3-6 kluczowych cech segmentu (zachowania, postawy, potrzeby)"
    )

    allocation_reasoning: str = Field(
        max_length=400,
        description="Zwięzłe uzasadnienie dlaczego taki count i demografia (max 400 znaków)"
    )

    graph_insights: List[GraphInsight] = Field(
        default_factory=list,
        max_items=5,
        description="Maksymalnie 5 najważniejszych insightów z Neo4j GraphRAG dla tego segmentu"
    )


class PersonaAllocationPlan(BaseModel):
    """Kompletny plan alokacji person z briefami."""

    total_personas: int = Field(
        ge=1,
        description="Całkowita liczba person do wygenerowania (suma wszystkich grup)"
    )

    overall_context: str = Field(
        max_length=800,
        description="Ogólny kontekst badania i populacji docelowej (max 800 znaków)"
    )

    groups: List[PersonaGroupAllocation] = Field(
        min_items=1,
        max_items=10,
        description="Lista grup person (1-10 segmentów). Każda grupa ma count, demographics, brief, characteristics, reasoning, graph_insights."
    )


# Eksportuj schemat JSON dla LLM structured output
ORCHESTRATION_PLAN_SCHEMA = PersonaAllocationPlan.model_json_schema()


# System prompt dla orchestration (krótszy, jasny)
ORCHESTRATION_SYSTEM_PROMPT = """Jesteś ekspertem od strategii alokacji person w badaniach rynkowych.

Twoim zadaniem jest stworzenie PLANU ALOKACJI określającej:
1. Ile person wygenerować w każdym segmencie
2. Jakie charakterystyki demograficzne powinny mieć
3. Dlaczego taka alokacja jest optymalna dla badania

ZASADY ALOKACJI:
- Segmenty powinny odzwierciedlać różnorodność populacji docelowej
- Liczba person w segmencie = reprezentatywność + istotność dla badania
- Maksymalnie 10 segmentów (najczęściej 3-5 optymalnie)
- Brief dla każdej grupy: 500-700 znaków (narracyjny, konkretny, actionable)
- Graph insights: max 5 najważniejszych z Neo4j (jeśli dostępne)

DEMOGRAFIA (BEZ income_bracket!):
- age: przedział wiekowy ("18-24", "25-34", "35-44", "45-54", "55+")
- gender: "kobieta" | "mężczyzna" | "mixed"
- education: poziom wykształcenia ("podstawowe", "średnie", "wyższe", "mixed")
- location: lokalizacja ("Warszawa", "Kraków", "mixed", "małe miasta", etc.)

BRIEF (500-700 ZNAKÓW - KLUCZOWE!):
Opisz segment w sposób narracyjny i konkretny:
- KTO to jest (demografia + psychografia)
- JAKIE ma potrzeby, zachowania, postawy
- DLACZEGO jest istotny dla badania
- CO go wyróżnia od innych segmentów

NIE używaj bullet points, pisz ciągłym tekstem.

SEGMENT CHARACTERISTICS (3-6 CECH):
Kluczowe cechy behawioralne/postawowe, np.:
- "Profesjonaliści z wielkich miast"
- "Młodzi prekariusze"
- "Stabilni rodzice 35-44"

ALLOCATION REASONING (MAX 400 ZNAKÓW):
Zwięzłe uzasadnienie:
- Dlaczego TAK wiele person w tym segmencie
- Jaki ma to związek z celami badania
- Jaką reprezentatywność zapewnia

GRAPH INSIGHTS (MAX 5):
Jeśli dostępne w kontekście, dodaj:
- type: typ węzła ("Wskaznik", "Obserwacja", "Trend")
- summary: opis max 300 znaków
- magnitude, confidence, time_period, source (jeśli dostępne)
- why_matters: dlaczego ważne dla tego segmentu

WALIDACJA:
- Suma counts wszystkich grup MUSI równać się total_personas
- Każda grupa MUSI mieć brief 500-700 znaków
- Każda grupa MUSI mieć allocation_reasoning
- Demographics NIE MAY zawierać income_bracket!

Zwróć TYLKO JSON zgodny ze schematem PersonaAllocationPlan."""


class OrchestrationPromptVersion(str, Enum):
    """Wersja orchestration prompt dla cache invalidation."""
    ORCHESTRATION_PLAN = "v1.0"
