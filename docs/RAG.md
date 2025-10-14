# 📚 System RAG - Retrieval-Augmented Generation

Kompletna dokumentacja systemu RAG używanego do wzbogacania generowania person realistycznym kontekstem o polskim społeczeństwie.

---

## 🎯 Przegląd

System RAG łączy **Hybrid Search** (vector + keyword) z **Graph RAG** (struktura wiedzy) aby dostarczać najbardziej relevantny kontekst:

- **Hybrid Search**: Semantic (embeddings) + Lexical (keywords) + RRF Fusion
- **Graph RAG**: Strukturalna wiedza w Neo4j (koncepty, wskaźniki, trendy, relacje)
- **Użycie**: Generator person pobiera kontekst o demografii, kulturze, wartościach w Polsce

---

## 📊 Architektura

```
User Query (profil demograficzny: wiek, płeć, wykształcenie, lokalizacja)
         ↓
    ┌────────────────────────────────────────────────┐
    │            HYBRID SEARCH (parallel)            │
    │  ┌──────────────────────┐  ┌─────────────────┐│
    │  │   Vector Search      │  │ Keyword Search  ││
    │  │ (Google embeddings)  │  │ (Neo4j fulltext)││
    │  │   768 dimensions     │  │   Lucene-based  ││
    │  └──────────────────────┘  └─────────────────┘│
    └────────────────────────────────────────────────┘
                   ↓              ↓
              ┌────────────────────────┐
              │   RRF Fusion (k=60)    │ Reciprocal Rank Fusion
              └────────────────────────┘
                        ↓
              Top K Results (domyślnie 5)
                        ↓
    ┌────────────────────────────────────────────────┐
    │              GRAPH RAG (optional)              │
    │  ┌────────────────────────────────────────────┐│
    │  │ LLM → Cypher Query → Neo4j Graph Execution ││
    │  │ (koncepty, wskaźniki, trendy, relacje)     ││
    │  └────────────────────────────────────────────┘│
    └────────────────────────────────────────────────┘
                        ↓
                Context → LLM Prompt
```

---

## 🔍 Hybrid Search

### 1. Vector Search (Semantic)

**Technologia:**
- Google Gemini `text-embedding-001` (768 wymiarów)
- Neo4j Vector Index `rag_document_embeddings`
- Cosine similarity

**Jak działa:**
1. Query → embedding (768-wymiarowy wektor)
2. Szuka podobnych embeddings w Neo4j
3. Zwraca dokumenty semantycznie podobne

**Przykład:**
```
Query: "Młoda osoba z wykształceniem wyższym w Warszawie"
Znajduje:
  ✓ "studentach uniwersytetów w stolicy"
  ✓ "absolwentach z dużych miast"
  ✓ "młodzieży akademickiej w aglomeracjach"
```

**Zalety:** Rozumie synonimość, kontekst semantyczny
**Wady:** Może pominąć precyzyjne słowa kluczowe, wolniejsze

---

### 2. Keyword Search (Lexical)

**Technologia:**
- Neo4j Fulltext Index `rag_fulltext_index`
- Lucene-based search

**Jak działa:**
1. Query → słowa kluczowe
2. Fulltext search w Neo4j
3. Zwraca dokumenty zawierające te słowa

**Przykład:**
```
Query: "Warszawa wykształcenie wyższe 25-34"
Znajduje dokumenty z:
  ✓ dokładnie słowo "Warszawa"
  ✓ dokładnie frazę "wykształcenie wyższe"
  ✓ dokładnie "25-34"
```

**Zalety:** Szybkie (~50ms), precyzyjne dopasowanie
**Wady:** Nie rozumie synonimów, brak kontekstu

---

### 3. RRF Fusion (Reciprocal Rank Fusion)

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

**Parametry:**
- `k = 60` (domyślnie) - typowa wartość w literaturze
- Wyższe k = mniejsza różnica między rankings
- Niższe k = większy wpływ top results

**Zalety:**
- Odporność na różne skale scores
- Promuje dokumenty znalezione przez obie metody
- Sprawdzone w praktyce (Elasticsearch)

---

## 🕸️ Graph RAG

### Koncepcja

Graph RAG ekstraktuje strukturalną wiedzę z dokumentów i zapisuje w grafie Neo4j jako węzły i relacje.

### Komponenty

**1. `RAGDocumentService`** - Ingest dokumentów, budowa grafu, Graph RAG queries
**2. `PolishSocietyRAG`** - Hybrid search dla generatora person
**3. API `/api/v1/rag/*`** - Upload, listowanie, zapytania

### Typy Węzłów

- **Observation** - Konkretne obserwacje, fakty z badań
- **Indicator** - Wskaźniki liczbowe, statystyki, metryki
- **Demographic** - Grupy demograficzne, populacje
- **Trend** - Trendy czasowe, zmiany w czasie
- **Location** - Miejsca geograficzne
- **Cause** / **Effect** - Przyczyny i skutki zjawisk

### Typy Relacji

- `DESCRIBES` - Opisuje cechę/właściwość
- `APPLIES_TO` - Dotyczy grupy/kategorii
- `SHOWS_TREND` - Pokazuje trend czasowy
- `LOCATED_IN` - Zlokalizowane w miejscu
- `CAUSED_BY` / `LEADS_TO` - Przyczyny i skutki
- `COMPARES_TO` - Porównanie

### Bogate Metadane Węzłów

Każdy węzeł zawiera:
- `description` - Szczegółowy opis (2-3 zdania)
- `summary` - Jednozdaniowe streszczenie
- `key_facts` - Lista kluczowych faktów (oddzielone średnikami)
- `source_context` - Cytat ze źródła (20-50 słów) dla weryfikowalności
- `time_period` - Okres czasu (format: "2020" lub "2018-2023")
- `magnitude` - Wartość z jednostką (np. "67%", "1.2 mln osób")
- `confidence_level` - "high" | "medium" | "low"
- `doc_id`, `chunk_index` - Metadane techniczne

### Bogate Metadane Relacji

- `confidence` - Pewność relacji 0.0-1.0 (string)
- `evidence` - Konkretny dowód z tekstu
- `strength` - "strong" | "moderate" | "weak"
- `doc_id`, `chunk_index` - Metadane techniczne

### Przepływ Ingestu

```
1. Upload PDF/DOCX → POST /api/v1/rag/documents/upload
2. Plik zapisany w data/documents/
3. Background task:
   a. PyPDFLoader/Docx2txtLoader wczytuje dokument
   b. RecursiveCharacterTextSplitter dzieli na chunki (2000 znaków, overlap 400)
   c. Dodanie metadanych (doc_id, chunk_index, title, country)
   d. LLMGraphTransformer ekstraktuje graf z bogatymi właściwościami
   e. _enrich_graph_nodes() wzbogaca i waliduje metadane
   f. Zapis chunków do Neo4j Vector Store z embeddingami
4. Status → completed, chunk_count w tabeli rag_documents
```

### Przepływ Graph RAG Query

```
1. POST /api/v1/rag/query/graph
   {"question": "Jakie są kluczowe trendy demograficzne w Polsce?"}
2. _generate_cypher_query() → LLM generuje Cypher query
3. Neo4j graph execution
4. Vector search jako wsparcie
5. LLM łączy graph context + vector context → answer
6. Response:
   {
     "answer": "...",
     "graph_context": [...],
     "vector_context": [...],
     "cypher_query": "MATCH (n:Trend)..."
   }
```

### Przykładowe Graph RAG Queries

```cypher
-- Znajdź największe wskaźniki
MATCH (n:Indicator)
WHERE n.magnitude IS NOT NULL
RETURN n.summary, n.magnitude, n.source_context
ORDER BY toFloat(split(n.magnitude, '%')[0]) DESC

-- Znajdź pewne fakty o temacie X
MATCH (n:Observation)
WHERE n.summary CONTAINS 'X' AND n.confidence_level = 'high'
RETURN n.description, n.key_facts, n.source_context

-- Jak X wpływa na Y? (silne relacje)
MATCH (cause)-[r:LEADS_TO]->(effect)
WHERE cause.summary CONTAINS 'X' AND effect.summary CONTAINS 'Y'
  AND r.strength = 'strong'
RETURN cause.summary, r.evidence, effect.summary, r.confidence
```

---

## ⚙️ Konfiguracja

W [app/core/config.py](../app/core/config.py):

```python
class Settings(BaseSettings):
    # Hybrid Search
    RAG_USE_HYBRID_SEARCH: bool = True      # Włącz hybrid search
    RAG_VECTOR_WEIGHT: float = 0.7          # Waga vector search (dla przyszłych eksperymentów)
    RAG_RRF_K: int = 60                     # RRF smoothing parameter
    RAG_TOP_K: int = 5                      # Liczba wyników

    # Chunking
    RAG_CHUNK_SIZE: int = 2000              # Rozmiar chunków (znaki)
    RAG_CHUNK_OVERLAP: int = 400            # Overlap między chunkami

    # GraphRAG Node Properties
    RAG_NODE_PROPERTIES_ENABLED: bool = True         # Włącz bogate metadane węzłów
    RAG_EXTRACT_SUMMARIES: bool = True               # Ekstrakcja summary
    RAG_EXTRACT_KEY_FACTS: bool = True               # Ekstrakcja key_facts
    RAG_RELATIONSHIP_CONFIDENCE: bool = True         # Confidence w relacjach
```

---

## 🚀 Setup i Inicjalizacja

### 1. Uruchom Neo4j

```bash
docker-compose up -d neo4j
```

### 2. Utwórz Indeksy (WYMAGANE!)

```bash
python scripts/init_neo4j_indexes.py
```

Tworzy:
- Vector index `rag_document_embeddings` (768 wymiarów, cosine)
- Fulltext index `rag_fulltext_index` (Lucene)

### 3. Upload Dokumentów

```bash
# Via API
curl -X POST http://localhost:8000/api/v1/rag/documents/upload \
  -F "file=@raport.pdf" \
  -F "title=Raport o polskim społeczeństwie 2023" \
  -F "country=Poland" \
  -F "date=2023"
```

### 4. Test Hybrid Search

```bash
python tests/manual/test_hybrid_search.py
```

---

## 📊 Wydajność

### Porównanie Metod

| Metoda | Czas na query | Jakość | Użycie |
|--------|---------------|--------|--------|
| Vector only | ~200ms | Dobra (semantic) | Ogólne queries |
| Keyword only | ~50ms | Dobra (lexical) | Precise queries |
| **Hybrid (RRF)** | **~250ms** | **Najlepsza** | **Produkcja** |
| Graph RAG | ~2-4s | Strukturalna | Analityczne queries |

### Wpływ na Generowanie Person

- **Bez RAG**: 30s dla 20 person, generyczne profile
- **Z RAG (vector only)**: 35s dla 20 person, realistyczne profile
- **Z RAG (hybrid)**: 40s dla 20 person, **najbardziej realistyczne** ✅
- **Z Graph RAG**: Użycie do specific insights, nie w critical path

**Trade-off**: +33% czas, ale znacznie wyższa jakość person.

---

## 🧪 Testowanie

### Manual Test

```bash
# Test hybrid search
python tests/manual/test_hybrid_search.py
```

Pokazuje:
- Vector search results
- Keyword search results
- RRF fused results
- Top citations z scores
- Fragment kontekstu

### Integration Tests

```bash
# Test pełnego pipeline ingest + Graph RAG
python -m pytest tests/test_rag_graph_properties.py -v
```

### API Testing

```bash
# Graph RAG query
curl -X POST http://localhost:8000/api/v1/rag/query/graph \
  -H "Content-Type: application/json" \
  -d '{"question": "Jakie są największe wskaźniki ubóstwa w Polsce?"}'
```

---

## 🔧 API Endpoints

### Upload Document

```http
POST /api/v1/rag/documents/upload
Content-Type: multipart/form-data

file: <PDF/DOCX file>
title: string
country: string (default: "Poland")
date: string (optional)
```

### List Documents

```http
GET /api/v1/rag/documents
```

### Delete Document

```http
DELETE /api/v1/rag/documents/{doc_id}
```

### RAG Query (Hybrid Search)

```http
POST /api/v1/rag/query
Content-Type: application/json

{
  "question": "string"
}
```

### Graph RAG Query

```http
POST /api/v1/rag/query/graph
Content-Type: application/json

{
  "question": "string"
}
```

---

## 🛠️ Implementacja

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

### Utworzenie Fulltext Index

```python
async def _ensure_fulltext_index(self):
    """Utwórz fulltext index jeśli nie istnieje"""
    driver.session().execute_write("""
        CREATE FULLTEXT INDEX rag_fulltext_index IF NOT EXISTS
        FOR (n:RAGChunk)
        ON EACH [n.text]
    """)
```

---

## 🐛 Troubleshooting

### Brak połączenia z Neo4j

```bash
docker-compose logs neo4j
docker-compose restart neo4j
curl http://localhost:7474  # Sprawdź Neo4j Browser
```

### Indeksy nie istnieją

```bash
python scripts/init_neo4j_indexes.py
# Verify: Neo4j Browser → SHOW INDEXES
```

### Wolne zapytania

- Sprawdź czy indeksy są w stanie `ONLINE`: `SHOW INDEXES`
- Vector index może być w `POPULATING` przez kilka minut po utworzeniu
- Zwiększ `RAG_TOP_K` dla lepszej jakości, zmniejsz dla szybkości

### Błędy ingestu

```bash
# Sprawdź logi
docker-compose logs api

# Sprawdź status dokumentu
curl http://localhost:8000/api/v1/rag/documents
# Status: "completed" | "processing" | "failed"
```

---

## 📚 Literatura i Referencje

1. **RRF Paper**: Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009). "Reciprocal rank fusion outperforms condorcet and individual rank learning methods"
2. **Elasticsearch Hybrid Search**: https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
3. **Neo4j Vector Search**: https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/
4. **Neo4j Fulltext**: https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/
5. **LangChain Graph RAG**: https://python.langchain.com/docs/use_cases/graph/

---

## 🔮 Przyszłe Ulepszenia

- [ ] Boost dla specific fields (title vs content)
- [ ] Query expansion (synonimy, related terms)
- [ ] User feedback loop (RLHF dla rankingu)
- [ ] A/B testing hybrid vs vector-only
- [ ] Cross-encoder reranking jako 4th stage
- [ ] Temporal reasoning w Graph RAG (analiza zmian w czasie)
- [ ] Multi-hop reasoning w grafie (ścieżki 2-3 węzłów)

---

**Ostatnia aktualizacja:** 2025-10-14
**Wersja:** 2.0 (połączony dokument RAG)
