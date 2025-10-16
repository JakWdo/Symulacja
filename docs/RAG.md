# System RAG - Retrieval-Augmented Generation w Market Research SaaS

System RAG (Retrieval-Augmented Generation) stanowi zaawansowany mechanizm wzbogacania generowanych person o precyzyjny, kontekstowy wgląd w polskie społeczeństwo. Łączy on dwie kluczowe strategie: Hybrid Search (semantyczne i leksykalne dopasowanie dokumentów) oraz Graph RAG (strukturalna wiedza z grafów), tworząc wielowarstwowy, inteligentny system pozyskiwania i przetwarzania informacji.

Nasza innowacyjna architektura pozwala na ekstrakcję nie tylko surowego tekstu, ale również złożonych relacji, trendów i wskaźników, które nadają wygenerowanym personom autentyczność i realizm.

## Architektura Systemu RAG

```
User Query (profil demograficzny: wiek, płeć, wykształcenie, lokalizacja)
         ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │                   DUAL-SOURCE RETRIEVAL                         │
    │  ┌────────────────────┐    ┌───────────────────────────┐  │
    │  │   HYBRID SEARCH    │    │   GRAPH RAG (CORE)        │  │
    │  │ ┌──────────────────┐   │ ┌───────────────────────┐ │  │
    │  │ │ Vector Search    │   │ │ Structural Knowledge  │ │  │
    │  │ │ (Semantic)       │   │ │ Cypher Queries        │ │  │
    │  │ └──────────────────┘   │ │ Wskaźniki, Trendy     │ │  │
    │  │ ┌──────────────────┐   │ │ Obserwacje, Przyczyny │ │  │
    │  │ │ Keyword Search   │   │ └───────────────────────┘ │  │
    │  │ │ (Lexical)        │   │                           │  │
    │  │ └──────────────────┘   │                           │  │
    │  │        ↓                │                           │  │
    │  │ RRF Fusion + Rerank    │                           │  │
    │  └────────────────────────┘    └───────────────────────┘  │
    └─────────────────────────────────────────────────────────────┘
                   ↓                             ↓
                   └─────────────┬───────────────┘
                                 ↓
                    ┌────────────────────────────┐
                    │   UNIFIED CONTEXT          │
                    │ Graph Knowledge + Chunks   │
                    │ (Enriched with graph data) │
                    └────────────────────────────┘
                                 ↓
                         Context → LLM Prompt
```

## Komponenty Systemu

### 1. Hybrid Search (PolishSocietyRAG)

#### Vector Search (Semantic)
- Technologia: Google Gemini `text-embedding-001` (768 wymiarów)
- Cosine similarity w Neo4j Vector Index
- Znajduje dokumenty semantycznie podobne

#### Keyword Search (Lexical)
- Fulltext index w Neo4j (Lucene-based)
- Precyzyjne dopasowanie słów kluczowych
- Szybkie wyszukiwanie (~50ms)

#### RRF Fusion
Algorytm łączący wyniki wyszukiwania semantycznego i leksykalnego:
```python
def rrf_fusion(vector_results, keyword_results, k=60):
    scores = {}
    for rank, doc in enumerate(vector_results):
        scores[doc] += 1 / (k + rank + 1)
    for rank, doc in enumerate(keyword_results):
        scores[doc] += 1 / (k + rank + 1)
    return sorted(scores, key=lambda x: scores[x], reverse=True)
```

### 2. Graph RAG (Neo4j)

#### Typy Węzłów
- **Obserwacja**: Fakty, przyczyny i skutki
- **Wskaźnik**: Statystyki, metryki
- **Demografia**: Grupy demograficzne
- **Trend**: Zmiany w czasie
- **Lokalizacja**: Miejsca geograficzne

#### Typy Relacji
- `OPISUJE`: Opisuje cechę/właściwość
- `DOTYCZY`: Dotyczy kategorii
- `POKAZUJE_TREND`: Trend czasowy
- `ZLOKALIZOWANY_W`: Lokalizacja
- `POWIAZANY_Z`: Ogólne powiązania

#### Metadane Węzłów
- `streszczenie`: Jednozdaniowe podsumowanie
- `skala`: Wartość z jednostką
- `pewnosc`: Poziom pewności danych
- `okres_czasu`: Zakres czasowy
- `kluczowe_fakty`: Maksymalnie 3 fakty

## Przepływ Ingestu Dokumentów

1. Upload dokumentu przez API
2. Podział na chunki (1000 znaków, 30% overlap)
3. Ekstrakcja embeddings
4. Zapis chunków i grafu w Neo4j
5. Wzbogacenie metadanych

## Kluczowe Metryki Wydajności

### Retrieval Quality
- **Precision@5**: >70%
- **Recall@8**: >80%
- **F1 Score**: >75%

### Latency
- Hybrid search: <250ms
- Z rerankingiem: <350ms
- Graph RAG query: <3s

## Przyszłe Ulepszenia

### Priorytet Średni (Q4 2025)
- Semantic chunking
- Lepsze dopasowanie węzłów grafu
- Uproszczenie prompt dla graph extraction

### Priorytet Niski (2026)
- Dynamiczny TOP_K
- Redukcja wymiarowości
- Dostosowany polski cross-encoder
- Pętla opinii użytkownika

**Ostatnia aktualizacja:** 2025-10-14
**Wersja:** 2.1