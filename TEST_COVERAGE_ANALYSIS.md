# Analiza Pokrycia Testami - Raport

**Data**: 2025-11-13
**Projekt**: Sight Platform
**Cel**: Pokrycie testami 85%+

---

## 📊 Podsumowanie Wykonawcze

### Status Ogólny
- ✅ **Pełne pokrycie**: `app/services/rag/search/hybrid_search_service.py`, `app/services/rag/documents/document_service.py`
- ⚠️ **Częściowe pokrycie**: `app/services/personas/orchestration/*` (główny przepływ testowany, moduły pomocnicze bez testów)
- ❌ **Brak pokrycia**: `app/services/dashboard/metrics/*` (większość modułów)

---

## 1. Personas/Orchestration - Częściowe Pokrycie

### ✅ Moduły Z Testami (w `tests/unit/test_persona_orchestration.py`)

1. **persona_orchestration.py** - PersonaOrchestrationService
   - ✅ Comprehensive Graph RAG context retrieval (8 parallel queries)
   - ✅ DemographicGroup brief generation (900-1200 znaków)
   - ✅ Graph insights extraction
   - ✅ Allocation reasoning
   - ✅ Timeout handling (30s dla graph queries)

2. **json_parser.py** - extract_json_from_response
   - ✅ Parsowanie JSON w markdown blocks
   - ✅ Parsowanie JSON w plain blocks
   - ✅ Parsowanie bare braces
   - ✅ Error handling dla invalid JSON

3. **prompt_builder.py** - build_orchestration_prompt
   - ✅ Struktura promptu (5 sekcji)
   - ✅ Includowanie graph context

### ❌ Moduły BEZ Testów (Krytyczne Luki)

1. **brief_cache.py** - Cache'owanie segment briefów
   - Funkcjonalność: Redis/in-memory cache dla segment_brief_service
   - Priorytet: **WYSOKI** (cache może powodować stale data)
   - Testy potrzebne:
     - Cache hit/miss scenarios
     - TTL expiration
     - Cache invalidation przy zmianie demographics

2. **brief_formatter.py** - Formatowanie briefów
   - Funkcjonalność: Formatowanie briefów dla LLM i UI
   - Priorytet: **ŚREDNI**
   - Testy potrzebne:
     - Truncation przy przekroczeniu max length
     - HTML escaping
     - Markdown rendering

3. **filtering_utils.py** - Filtry demograficzne
   - Funkcjonalność: Filtrowanie person po kryteriach demograficznych
   - Priorytet: **WYSOKI** (używane w allocation logic)
   - Testy potrzebne:
     - Age range filtering
     - Gender filtering
     - Education level filtering
     - Complex AND/OR filters

4. **graph_context_fetcher.py** - Pobieranie kontekstu z Graph RAG
   - Funkcjonalność: Wrapper dla hybrid_search queries
   - Priorytet: **ŚREDNI** (testowane pośrednio przez persona_orchestration)
   - Testy potrzebne:
     - Query construction
     - Deduplication
     - Timeout handling

5. **segment_brief_service.py** - Generowanie briefów per segment
   - Funkcjonalność: LLM-based brief generation
   - Priorytet: **KRYTYCZNY** (core business logic)
   - Testy potrzebne:
     - Brief length validation (900-1200 znaków)
     - Educational tone verification
     - Graph insights integration
     - Retry logic przy LLM errors

6. **segment_context_generator.py** - Generowanie kontekstu dla segmentów
   - Funkcjonalność: Przygotowanie contextu demograficznego per segment
   - Priorytet: **WYSOKI**
   - Testy potrzebne:
     - Context aggregation z multiple sources
     - Deduplication
     - Relevance ranking

7. **segment_naming.py** - Nazwy segmentów demograficznych
   - Funkcjonalność: Generowanie czytelnych nazw segmentów ("Młodzi profesjonaliści 25-34")
   - Priorytet: **NISKI** (UI-only, nie wpływa na logikę)
   - Testy potrzebne:
     - Consistency nazewnictwa
     - Edge cases (empty segments, single demographics)

8. **models.py** - Dataclasses dla orchestration
   - Funkcjonalność: PersonaAllocationPlan, DemographicGroup, GraphInsight
   - Priorytet: **NISKI** (pydantic validation coverage wystarczająca)
   - Testy potrzebne:
     - Validation edge cases (negative counts, invalid JSON)

---

## 2. RAG/Graph - Częściowe Pokrycie

### ✅ Moduły Z Testami (w `tests/unit/test_rag_graph_service.py`)

1. **graph_service.py** - GraphRAGService (główny serwis)
   - ✅ Enrich graph nodes (metadata validation)
   - ✅ Cypher query generation
   - ✅ Answer question (Graph RAG pipeline)

### ❌ Moduły BEZ Testów

1. **graph_enrichment.py** - Wzbogacanie grafu
   - Funkcjonalność: Dodawanie metadata do nodes/relationships
   - Priorytet: **ŚREDNI**
   - Testy potrzebne:
     - Metadata validation
     - Relationship enrichment
     - Duplicate detection

2. **graph_formatter.py** - Formatowanie output Graph RAG
   - Funkcjonalność: Przekształcanie Cypher results na JSON/markdown
   - Priorytet: **ŚREDNI**
   - Testy potrzebne:
     - JSON serialization
     - Markdown rendering
     - Null handling

3. **insights_extractor.py** - Ekstrakcja insightów z grafu
   - Funkcjonalność: LLM-based insight extraction z graph data
   - Priorytet: **KRYTYCZNY** (core business logic)
   - Testy potrzebne:
     - Insight structure validation
     - Confidence scoring
     - Why_matters generation
     - Edge cases (empty graph, no insights)

4. **query_builder.py** - Budowa Cypher queries
   - Funkcjonalność: Programmatic Cypher query construction
   - Priorytet: **WYSOKI** (bezpieczeństwo - injection prevention)
   - Testy potrzebne:
     - Query syntax validation
     - Parameter binding (injection prevention)
     - Complex queries (MATCH, WHERE, RETURN)
     - Edge cases (empty WHERE, null parameters)

5. **traversal.py** - Graph traversal algorithms
   - Funkcjonalność: Przechodzenie przez graf (BFS, DFS, shortest path)
   - Priorytet: **ŚREDNI**
   - Testy potrzebne:
     - BFS/DFS correctness
     - Cycle detection
     - Max depth limiting

---

## 3. Dashboard/Metrics - Brak Pokrycia ❌

### ❌ Wszystkie Moduły BEZ Testów Jednostkowych

1. **health_service.py** - Health checks
   - Funkcjonalność: DB/Redis/Neo4j health monitoring
   - Priorytet: **KRYTYCZNY** (produkcyjny monitoring)
   - Testy potrzebne:
     - All services healthy scenario
     - Individual service failures
     - Timeout handling
     - Degraded state detection

2. **metrics_aggregator.py** - Agregacja metryk
   - Funkcjonalność: Agregacja usage/cost/performance metrics
   - Priorytet: **WYSOKI** (billing logic)
   - Testy potrzebne:
     - Time-based aggregation (daily, monthly)
     - Cost calculation accuracy
     - Token counting
     - Edge cases (no data, negative values)

3. **metrics_service.py** - Główny serwis metryk
   - Funkcjonalność: Orchestration layer dla metrics collection
   - Priorytet: **WYSOKI**
   - Testy potrzebne:
     - Metrics collection flow
     - Async aggregation
     - Cache invalidation
     - Rate limiting

---

## 4. Priorytetyzacja Testów (wg Business Impact)

### P0 - Krytyczne (Brak = Ryzyko Finansowe/Bezpieczeństwa)
1. ✅ `segment_brief_service.py` - Core business logic generacji briefów
2. ✅ `query_builder.py` - SQL injection prevention
3. ✅ `insights_extractor.py` - Core business logic Graph RAG
4. ✅ `health_service.py` - Production monitoring
5. ✅ `metrics_aggregator.py` - Billing accuracy

### P1 - Wysokie (Brak = Możliwe Błędy w Produkcji)
6. ✅ `brief_cache.py` - Stale data risk
7. ✅ `filtering_utils.py` - Incorrect allocation logic
8. ✅ `segment_context_generator.py` - Context quality
9. ✅ `metrics_service.py` - Metrics collection reliability

### P2 - Średnie (Brak = Możliwe Edge Case Failures)
10. ✅ `graph_enrichment.py`
11. ✅ `graph_formatter.py`
12. ✅ `traversal.py`
13. ✅ `brief_formatter.py`
14. ✅ `graph_context_fetcher.py`

### P3 - Niskie (UI/DX, nie wpływa na core logic)
15. `segment_naming.py`
16. `models.py` (Pydantic validation wystarczająca)

---

## 5. Szacowanie Effort

### Testy P0 (5 modułów)
- Effort: **3-4 dni robocze**
- Testy per moduł: 8-12 testów
- Pokrycie: 85%+ dla P0 modułów

### Testy P1 (4 moduły)
- Effort: **2-3 dni robocze**
- Testy per moduł: 6-8 testów
- Pokrycie: 80%+ dla P1 modułów

### Testy P2 (5 modułów)
- Effort: **2 dni robocze**
- Testy per moduł: 4-6 testów
- Pokrycie: 70%+ dla P2 modułów

**Total Effort**: 7-9 dni roboczych dla pełnego pokrycia 85%+

---

## 6. Rekomendacje

### Natychmiastowe Działania
1. ✅ Napisać testy P0 (segment_brief_service, query_builder, insights_extractor, health_service, metrics_aggregator)
2. ⚠️ Setup CI/CD coverage gating: Fail build jeśli pokrycie < 85%
3. ⚠️ Dodać coverage badge do README.md

### Krótkoterminowe (1-2 tygodnie)
4. Napisać testy P1
5. Setup pytest-cov w Cloud Build pipeline
6. Dokumentować test patterns w `docs/QA.md`

### Długoterminowe
7. Napisać testy P2
8. Setup mutation testing (mutpy) dla critical paths
9. Performance benchmarking dla RAG queries

---

## 7. Istniejące Testy - Podsumowanie

### Testy Jednostkowe (tests/unit/)
- ✅ `test_persona_orchestration.py` (545 linii, comprehensive)
- ✅ `test_rag_graph_service.py` (partial coverage)
- ✅ `test_rag_hybrid_search_service.py` (comprehensive)
- ✅ `test_rag_document_service.py` (comprehensive)
- ⚠️ `test_datetime_timezone.py` (tylko utils, nie metrics)

### Testy Integracyjne (tests/integration/)
- ✅ `test_dashboard_api.py` (API endpoints, nie unit logic)
- ✅ `test_personas_api_integration.py` (end-to-end, nie unit)

### Testy E2E (tests/e2e/)
- ✅ `test_orchestration_smoke.py` (smoke tests)

**Obserwacja**: Dobra struktura testów E2E i integration, ale luki w unit tests dla modułów pomocniczych.

---

## 8. Template Testu (Do Kopiowania)

```python
"""
Testy jednostkowe dla {MODULE_NAME}

Zakres testów:
- {FUNCTIONALITY_1}
- {FUNCTIONALITY_2}
- Edge cases i error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.{path}.{module} import {Class/Function}


class Test{FunctionalityName}:
    """Testy dla {specific functionality}"""

    async def test_{happy_path_scenario}(self):
        """Test: {Clear description of what is tested}"""
        # Arrange
        service = {Class}()

        # Act
        result = await service.{method}(param1, param2)

        # Assert
        assert result is not None
        assert isinstance(result, {ExpectedType})

    async def test_{edge_case_scenario}(self):
        """Test: {Edge case description}"""
        # Arrange
        service = {Class}()

        # Act & Assert
        with pytest.raises({ExceptionType}):
            await service.{method}(invalid_param)

    async def test_{error_handling}(self):
        """Test: {Error scenario}"""
        # ... test implementation
```

---

## 9. Next Steps

1. ✅ **Dzisiaj**: Stworzyć branch `feature/test-coverage-p0` i rozpocząć testy P0
2. ⏳ **Jutro**: Dokończyć testy P0, review + merge
3. ⏳ **Następny tydzień**: Testy P1 i P2, CI/CD coverage gating

---

**Autor**: Claude Code
**Status**: ✅ Analiza zakończona, gotowy do implementacji
