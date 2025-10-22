"""
Prompty dla systemu RAG (Graph RAG, hybrid search, knowledge graph).

Ten moduł zawiera prompty używane w procesie RAG:
- CYPHER_GENERATION_SYSTEM_PROMPT - Generowanie zapytań Cypher z pytań użytkownika
- GRAPH_RAG_ANSWER_SYSTEM_PROMPT - Odpowiadanie na pytania z kontekstem grafowym

Użycie:
    from app.core.prompts.rag_prompts import CYPHER_GENERATION_SYSTEM_PROMPT
"""

# ═══════════════════════════════════════════════════════════════════════════════
# CYPHER QUERY GENERATION (GraphRAGService)
# ═══════════════════════════════════════════════════════════════════════════════

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


CYPHER_GENERATION_USER_PROMPT_TEMPLATE = "Pytanie: {question}"


# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH RAG ANSWER GENERATION (GraphRAGService)
# ═══════════════════════════════════════════════════════════════════════════════

GRAPH_RAG_ANSWER_SYSTEM_PROMPT = """
Jesteś ekspertem od analiz społecznych. Odpowiadasz wyłącznie na
podstawie dostarczonego kontekstu z grafu i dokumentów. Udzielaj
precyzyjnych, zweryfikowalnych odpowiedzi po polsku.
""".strip()


GRAPH_RAG_ANSWER_USER_PROMPT_TEMPLATE = "Pytanie: {question}\n\nKontekst:\n{context}"


# ═══════════════════════════════════════════════════════════════════════════════
# DEMOGRAPHIC CONTEXT CYPHER QUERY
# ═══════════════════════════════════════════════════════════════════════════════

DEMOGRAPHIC_CONTEXT_CYPHER_QUERY = """
// Parametry: $search_terms - lista słów kluczowych do matchingu
// UWAGA: Schema używa POLSKICH property names (streszczenie, skala, pewnosc, etc.)

// 1. Znajdź Wskaźniki (preferuj wysoką pewność jeśli istnieje)
// Case-insensitive search
MATCH (n:Wskaznik)
WHERE ANY(term IN $search_terms WHERE toLower(n.streszczenie) CONTAINS toLower(term))
   OR ANY(term IN $search_terms WHERE toLower(n.kluczowe_fakty) CONTAINS toLower(term))
WITH n, n.pewnosc AS pewnosc
ORDER BY
  CASE n.pewnosc
    WHEN 'wysoka' THEN 3
    WHEN 'srednia' THEN 2
    WHEN 'niska' THEN 1
    ELSE 0
  END DESC
LIMIT 10
RETURN
  'Wskaznik' AS type,
  n.streszczenie AS streszczenie,
  n.skala AS skala,
  n.pewnosc AS pewnosc,
  n.okres_czasu AS okres_czasu,
  n.kluczowe_fakty AS kluczowe_fakty,
  n.document_title AS source

UNION ALL

// 2. Znajdź Obserwacje
MATCH (o:Obserwacja)
WHERE ANY(term IN $search_terms WHERE toLower(o.streszczenie) CONTAINS toLower(term))
   OR ANY(term IN $search_terms WHERE toLower(o.kluczowe_fakty) CONTAINS toLower(term))
WITH o
ORDER BY
  CASE o.pewnosc
    WHEN 'wysoka' THEN 3
    WHEN 'srednia' THEN 2
    WHEN 'niska' THEN 1
    ELSE 0
  END DESC
LIMIT 10
RETURN
  'Obserwacja' AS type,
  o.streszczenie AS streszczenie,
  null AS skala,
  o.pewnosc AS pewnosc,
  o.okres_czasu AS okres_czasu,
  o.kluczowe_fakty AS kluczowe_fakty,
  o.document_title AS source

UNION ALL

// 3. Znajdź Trendy
MATCH (t:Trend)
WHERE ANY(term IN $search_terms WHERE toLower(t.streszczenie) CONTAINS toLower(term))
   OR ANY(term IN $search_terms WHERE toLower(t.kluczowe_fakty) CONTAINS toLower(term))
WITH t
LIMIT 5
RETURN
  'Trend' AS type,
  t.streszczenie AS streszczenie,
  null AS skala,
  t.pewnosc AS pewnosc,
  t.okres_czasu AS okres_czasu,
  t.kluczowe_fakty AS kluczowe_fakty,
  t.document_title AS source
"""


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def build_cypher_generation_prompt(question: str, graph_schema: str) -> dict:
    """
    Helper do budowania prompta dla generowania Cypher.

    Args:
        question: Pytanie użytkownika
        graph_schema: Schema grafu Neo4j

    Returns:
        Dict z messages dla ChatPromptTemplate
    """
    return {
        "question": question,
        "graph_schema": graph_schema
    }


def build_graph_rag_answer_prompt(question: str, graph_context: list, vector_context_docs: list) -> dict:
    """
    Helper do budowania prompta dla odpowiedzi Graph RAG.

    Args:
        question: Pytanie użytkownika
        graph_context: Wyniki zapytania Cypher
        vector_context_docs: Dokumenty z wyszukiwania wektorowego

    Returns:
        Dict z messages dla ChatPromptTemplate
    """
    # Agregacja kontekstu
    final_context = "KONTEKST Z GRAFU WIEDZY:\n" + str(graph_context)
    final_context += "\n\nFRAGMENTY Z DOKUMENTÓW:\n"
    for doc in vector_context_docs:
        final_context += f"- {doc.page_content}\n"

    return {
        "question": question,
        "context": final_context
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GRAPH TRANSFORMER CONFIGURATION (LLMGraphTransformer)
# ═══════════════════════════════════════════════════════════════════════════════
# Te stałe definiują strukturę grafu wiedzy tworzonego z dokumentów RAG.
# Używane w: app/services/rag/rag_document_service.py

GRAPH_TRANSFORMER_ALLOWED_NODES = [
    "Obserwacja",   # Fakty, obserwacje (merge Przyczyna, Skutek tutaj)
    "Wskaznik",     # Wskaźniki liczbowe, statystyki
    "Demografia",   # Grupy demograficzne
    "Trend",        # Trendy czasowe, zmiany w czasie
    "Lokalizacja",  # Miejsca geograficzne
]

GRAPH_TRANSFORMER_ALLOWED_RELATIONSHIPS = [
    "OPISUJE",           # Opisuje cechę/właściwość
    "DOTYCZY",           # Dotyczy grupy/kategorii
    "POKAZUJE_TREND",    # Pokazuje trend czasowy
    "ZLOKALIZOWANY_W",   # Zlokalizowane w miejscu
    "POWIAZANY_Z",       # Ogólne powiązanie (merge: przyczynowość, porównania)
]

GRAPH_TRANSFORMER_NODE_PROPERTIES = [
    "streszczenie",     # MUST: Jednozdaniowe podsumowanie (max 150 znaków)
    "skala",            # Wielkość/wartość z jednostką (np. "67%", "1.2 mln")
    "pewnosc",          # MUST: Pewność: "wysoka", "srednia", "niska"
    "okres_czasu",      # Okres czasu (YYYY lub YYYY-YYYY)
    "kluczowe_fakty",   # Opcjonalnie: max 3 fakty (separated by semicolons)
]

GRAPH_TRANSFORMER_RELATIONSHIP_PROPERTIES = [
    "sila",  # Siła relacji: "silna", "umiarkowana", "slaba"
]

GRAPH_TRANSFORMER_ADDITIONAL_INSTRUCTIONS = """
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
