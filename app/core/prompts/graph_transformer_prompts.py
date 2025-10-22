"""
Prompty i konfiguracja dla LLMGraphTransformer (budowa grafu wiedzy).

Zawiera:
- GRAPH_ALLOWED_NODES – dozwolone typy węzłów
- GRAPH_ALLOWED_RELATIONSHIPS – dozwolone typy relacji
- GRAPH_NODE_PROPERTIES – właściwości węzłów (polskie nazwy)
- GRAPH_RELATIONSHIP_PROPERTIES – właściwości relacji
- GRAPH_ADDITIONAL_INSTRUCTIONS – szczegółowe instrukcje dla transformera
"""

# Dozwolone typy węzłów w grafie wiedzy
GRAPH_ALLOWED_NODES = [
    "Obserwacja",   # Fakty, obserwacje (merge Przyczyna, Skutek tutaj)
    "Wskaznik",     # Wskaźniki liczbowe, statystyki
    "Demografia",   # Grupy demograficzne
    "Trend",        # Trendy czasowe, zmiany w czasie
    "Lokalizacja",  # Miejsca geograficzne
]


# Dozwolone typy relacji w grafie
GRAPH_ALLOWED_RELATIONSHIPS = [
    "OPISUJE",           # Opisuje cechę/właściwość
    "DOTYCZY",           # Dotyczy grupy/kategorii
    "POKAZUJE_TREND",    # Pokazuje trend czasowy
    "ZLOKALIZOWANY_W",   # Zlokalizowane w miejscu
    "POWIAZANY_Z",       # Ogólne powiązanie (merge: przyczynowość, porównania)
]


# Właściwości węzłów (polskie nazwy, zgodne z resztą systemu)
GRAPH_NODE_PROPERTIES = [
    "streszczenie",     # MUST: Jednozdaniowe podsumowanie (max 150 znaków)
    "skala",            # Wielkość/wartość z jednostką (np. "67%", "1.2 mln")
    "pewnosc",          # MUST: "wysoka" | "srednia" | "niska"
    "okres_czasu",      # Okres czasu (YYYY lub YYYY-YYYY)
    "kluczowe_fakty",   # Opcjonalnie: max 3 fakty (oddzielone średnikami)
]


# Właściwości relacji
GRAPH_RELATIONSHIP_PROPERTIES = [
    "sila",  # Siła relacji: "silna", "umiarkowana", "slaba"
]


# Dodatkowe instrukcje dla LLMGraphTransformer (po polsku)
GRAPH_ADDITIONAL_INSTRUCTIONS = (
    """
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
Węzeł: {{
  type: "Wskaznik",
  streszczenie: "Stopa zatrudnienia kobiet 25-34 z wyższym wykształceniem",
  skala: "78.4%",
  pewnosc: "wysoka",
  okres_czasu: "2022",
  kluczowe_fakty: "wysoka stopa zatrudnienia; kobiety młode; wykształcenie wyższe"
}}

PRZYKŁAD 2 - Obserwacja:
Tekst: "Młodzi mieszkańcy dużych miast coraz częściej wynajmują mieszkania zamiast kupować"
Węzeł: {{
  type: "Obserwacja",
  streszczenie: "Młodzi w miastach preferują wynajem nad zakup mieszkań",
  pewnosc: "srednia",
  kluczowe_fakty: "młodzi dorośli; duże miasta; wynajem mieszkań"
}}

PRZYKŁAD 3 - Trend:
Tekst: "Od 2018 do 2023 wzrósł odsetek osób pracujących zdalnie z 12% do 31%"
Węzeł: {{
  type: "Trend",
  streszczenie: "Wzrost pracy zdalnej w Polsce",
  skala: "12% → 31%",
  pewnosc: "wysoka",
  okres_czasu: "2018-2023",
  kluczowe_fakty: "praca zdalna; wzrost; pandemia"
}}

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
"""
)

