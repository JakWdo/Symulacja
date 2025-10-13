# RAG Hybrid Search - Dokumentacja Techniczna

## Przegląd

System RAG (Retrieval-Augmented Generation) używa **hybrid search** aby znaleźć najbardziej relevantne fragmenty dokumentów do wzbogacenia generowania person. Hybrid search łączy dwie komplementarne metody:

1. **Vector Search** (semantic) - rozumie znaczenie i kontekst
2. **Keyword Search** (lexical) - precyzyjne dopasowanie słów kluczowych
3. **RRF Fusion** - inteligentnie łączy oba wyniki

## Architektura

```
User Query (demograficzny profil)
         ↓
    ┌────────────────┐
    │ Query Builder  │  Konstruuje zapytanie po polsku
    └────────────────┘
         ↓
    ┌────────────────────────────────────┐
    │     HYBRID SEARCH (parallel)       │
    │  ┌──────────────┐  ┌─────────────┐│
    │  │Vector Search │  │Keyword Search││
    │  │(embeddings)  │  │(fulltext)   ││
    │  └──────────────┘  └─────────────┘│
    └────────────────────────────────────┘
         ↓              ↓
    ┌────────────────────────┐
    │   RRF Fusion           │  Reciprocal Rank Fusion
    │   (combine rankings)   │
    └────────────────────────┘
         ↓
    Top K Results → Context → LLM Prompt
```

## 1. Vector Search (Semantic)

**Co robi:**
- Zamienia query na embedding (vector 768-wymiarowy)
- Szuka podobnych embeddings w Neo4j Vector Index
- Zwraca dokumenty semantycznie podobne (niekoniecznie te same słowa)

**Technologia:**
- Google Gemini `text-embedding-004`
- Neo4j Vector Index (cosine similarity)
- Wymiar: 768

**Przykład:**
```python
Query: "Młoda osoba z wykształceniem wyższym w Warszawie"
Znajduje dokumenty o:
  ✓ "studentach uniwersytetów w stolicy"
  ✓ "absolwentach z dużych miast"
  ✓ "młodzieży akademickiej w aglomeracjach"
```

**Zalety:**
- Rozumie synonimość (student = młoda osoba z uniwersytetu)
- Znajduje koncepcyjnie podobne fragmenty
- Działa dobrze dla ogólnych zapytań

**Wady:**
- Może pominąć precyzyjne słowa kluczowe
- Wolniejsze (wymaga generowania embeddings)

## 2. Keyword Search (Lexical)

**Co robi:**
- Używa Neo4j Fulltext Index
- Szuka dokładnych dopasowań słów kluczowych
- Zwraca dokumenty zawierające te słowa

**Technologia:**
- Neo4j Fulltext Index na polu `text`
- Lucene-based search
- Index name: `rag_fulltext_index`

**Przykład:**
```python
Query: "Warszawa wykształcenie wyższe 25-34"
Znajduje dokumenty zawierające:
  ✓ dokładnie słowo "Warszawa"
  ✓ dokładnie frazę "wykształcenie wyższe"
  ✓ dokładnie liczby "25-34"
```

**Zalety:**
- Szybkie (index lookup)
- Precyzyjne dopasowanie terminów
- Działa dobrze dla specific queries

**Wady:**
- Nie rozumie synonimów
- Brak kontekstu semantycznego
- Wymaga dokładnych słów

## 3. RRF Fusion (Reciprocal Rank Fusion)

**Co robi:**
- Łączy wyniki z vector i keyword search
- Używa rankingu zamiast scores (odporność na różne skale)
- Formuła: `score = 1 / (k + rank)`

**Algorytm:**
```python
def rrf_fusion(vector_results, keyword_results, k=60):
    scores = {}

    # Score z vector search (rank-based)
    for rank, doc in enumerate(vector_results):
        scores[doc] += 1 / (k + rank + 1)

    # Score z keyword search (rank-based)
    for rank, doc in enumerate(keyword_results):
        scores[doc] += 1 / (k + rank + 1)

    # Sortuj po combined score
    return sorted(scores, key=lambda x: scores[x], reverse=True)
```

**Parametr k:**
- `k = 60` (domyślnie) - typowa wartość w literaturze
- Wyższe k = mniejsza różnica między rankings
- Niższe k = większy wpływ top results

**Przykład:**
```
Vector Search Rankings:        Keyword Search Rankings:
1. Doc A (score 0.95)           1. Doc C (score 45.2)
2. Doc B (score 0.89)           2. Doc A (score 32.1)
3. Doc C (score 0.72)           3. Doc D (score 28.5)

RRF Fusion:
Doc A: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325 ✓ BEST
Doc B: 1/(60+2) = 0.0161
Doc C: 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323
Doc D: 1/(60+3) = 0.0159
```

**Zalety:**
- Odporność na różne skale scores
- Promuje dokumenty znalezione przez obie metody
- Sprawdzone w praktyce (używane przez Elasticsearch)

## Implementacja

### Utworzenie Fulltext Index

Fulltext index jest automatycznie tworzony przy starcie `PolishSocietyRAG`:

```python
async def _ensure_fulltext_index(self):
    """Utwórz fulltext index jeśli nie istnieje"""
    driver.session().execute_write("""
        CREATE FULLTEXT INDEX rag_fulltext_index IF NOT EXISTS
        FOR (n:RAGChunk)
        ON EACH [n.text]
    """)
```

### Workflow Hybrid Search

```python
async def get_demographic_insights(...):
    # 1. Vector search (top 10 dla fusion)
    vector_results = await vector_store.asimilarity_search_with_score(
        query, k=RAG_TOP_K * 2
    )

    # 2. Keyword search (top 10 dla fusion)
    keyword_results = await _keyword_search(query, k=RAG_TOP_K * 2)

    # 3. RRF Fusion
    fused_results = _rrf_fusion(vector_results, keyword_results, k=60)

    # 4. Użyj top 5 fused results
    final_results = fused_results[:RAG_TOP_K]

    return build_context(final_results)
```

## Konfiguracja

W [app/core/config.py](../app/core/config.py):

```python
class Settings(BaseSettings):
    # Hybrid search on/off
    RAG_USE_HYBRID_SEARCH: bool = True

    # Waga vector vs keyword (nieużywane w RRF, ale do przyszłych eksperymentów)
    RAG_VECTOR_WEIGHT: float = 0.7

    # RRF k parameter (60 = standard)
    RAG_RRF_K: int = 60

    # Liczba wyników do zwrócenia
    RAG_TOP_K: int = 5
```

## Wydajność

### Porównanie Czasów

| Metoda | Czas na query | Jakość |
|--------|---------------|--------|
| Vector only | ~200ms | Dobra (semantic) |
| Keyword only | ~50ms | Dobra (lexical) |
| **Hybrid (RRF)** | **~250ms** | **Najlepsza** |

### Wpływ na Generowanie Person

- **Bez RAG**: ~30s dla 20 person, generyczne profile
- **Z RAG (vector only)**: ~35s dla 20 person, realistyczne profile
- **Z RAG (hybrid)**: ~40s dla 20 person, **najbardziej realistyczne profile**

Trade-off: +33% czas, ale znacznie wyższa jakość i realność person.

## Testowanie

```bash
# Test hybrid search z przykładowym query
python scripts/test_hybrid_search.py
```

Skrypt pokazuje:
- Vector search results
- Keyword search results
- RRF fused results
- Top citations z scores
- Fragment kontekstu

## Literatura

1. **RRF Paper**: Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009). "Reciprocal rank fusion outperforms condorcet and individual rank learning methods"
2. **Elasticsearch Hybrid Search**: https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
3. **Neo4j Fulltext**: https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/

## Przyszłe Ulepszenia

- [ ] Boost dla specific fields (title vs content)
- [ ] Query expansion (synonimy, related terms)
- [ ] User feedback loop (RLHF dla rankingu)
- [ ] A/B testing hybrid vs vector-only
- [ ] Cross-encoder reranking jako 4th stage
