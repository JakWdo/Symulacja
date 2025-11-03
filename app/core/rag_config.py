"""
Configuration constants for RAG system (Graph Transformer, Neo4j schema, etc.)

This module contains configuration constants used by the RAG system:
- Graph transformer configuration (allowed nodes, relationships, properties)
- Neo4j schema definitions
- Cypher query templates for demographic context

These are CONFIGURATION constants, not prompts. For RAG prompts, see config/prompts/rag/
"""

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
