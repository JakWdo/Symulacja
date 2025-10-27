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
