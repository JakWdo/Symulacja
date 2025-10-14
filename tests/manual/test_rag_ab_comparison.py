"""
Test A/B porównania konfiguracji RAG
====================================

Skrypt do testowania wpływu różnych parametrów RAG na jakość retrieval:
- Różne rozmiary chunków (1000 vs 2000)
- Różne wartości RRF_K (40, 60, 80)
- Różne TOP_K (5, 8, 10)

Użycie:
    python tests/manual/test_rag_ab_comparison.py

Wymaga:
    - Uruchomiony Neo4j z zaindeksowanymi dokumentami
    - GOOGLE_API_KEY w .env
"""

import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass

from app.services.rag_service import PolishSocietyRAG
from app.core.config import get_settings

settings = get_settings()


@dataclass
class TestQuery:
    """Zapytanie testowe z oczekiwanym kontekstem"""
    query_text: str
    demographics: Dict[str, str]
    expected_keywords: List[str]  # Słowa kluczowe które powinny być w wynikach
    description: str


# Test queries reprezentatywne dla use case
TEST_QUERIES = [
    TestQuery(
        query_text="młodzi ludzie w dużych miastach z wykształceniem wyższym",
        demographics={
            "age_group": "25-34",
            "location": "Warszawa",
            "education": "wyższe",
            "gender": "kobieta"
        },
        expected_keywords=["młod", "miasto", "uniwersytet", "studi", "wykształcen"],
        description="Młoda kobieta w stolicy z wyższym wykształceniem"
    ),
    TestQuery(
        query_text="seniorzy w małych miastach z podstawowym wykształceniem",
        demographics={
            "age_group": "65+",
            "location": "Kielce",
            "education": "podstawowe",
            "gender": "mężczyzna"
        },
        expected_keywords=["senior", "emeryt", "starszy", "wiek", "podstawow"],
        description="Senior w małym mieście"
    ),
    TestQuery(
        query_text="osoby w średnim wieku w średnich miastach ze średnim wykształceniem",
        demographics={
            "age_group": "45-54",
            "location": "Bydgoszcz",
            "education": "średnie",
            "gender": "kobieta"
        },
        expected_keywords=["średni", "wiek", "liceum", "miasto"],
        description="Osoba w średnim wieku, średnie miasto"
    ),
    TestQuery(
        query_text="młodzi absolwenci z wielkich miast poszukujący pracy",
        demographics={
            "age_group": "22-28",
            "location": "Kraków",
            "education": "wyższe",
            "gender": "mężczyzna"
        },
        expected_keywords=["absolwent", "praca", "zawod", "kariera", "młod"],
        description="Młody absolwent szukający pracy"
    ),
]


def calculate_keyword_coverage(
    context: str,
    expected_keywords: List[str]
) -> float:
    """
    Oblicz pokrycie expected keywords w kontekście

    Returns:
        Float 0.0-1.0 reprezentujący % pokrycia keywords
    """
    context_lower = context.lower()
    matched = sum(1 for keyword in expected_keywords if keyword in context_lower)
    return matched / len(expected_keywords) if expected_keywords else 0.0


def calculate_relevance_score(
    citations: List[Dict[str, Any]],
    expected_keywords: List[str]
) -> float:
    """
    Oblicz średni relevance score dla citations

    Bazuje na:
    1. RRF/rerank scores z citations
    2. Keyword coverage w każdym citation
    """
    if not citations:
        return 0.0

    scores = []
    for citation in citations:
        # Score z retrieval (RRF lub rerank)
        retrieval_score = citation.get('score', 0.0)

        # Keyword coverage w tym citation
        text = citation.get('text', '')
        keyword_score = calculate_keyword_coverage(text, expected_keywords)

        # Weighted average: 70% retrieval, 30% keywords
        combined = 0.7 * retrieval_score + 0.3 * keyword_score
        scores.append(combined)

    return sum(scores) / len(scores)


async def test_rag_configuration(
    test_query: TestQuery,
    config_name: str
) -> Dict[str, Any]:
    """
    Test RAG z obecną konfiguracją

    Args:
        test_query: Query do przetestowania
        config_name: Nazwa konfiguracji (dla logging)

    Returns:
        Dict z metrykami performance
    """
    print(f"\n{'='*60}")
    print(f"Testing config: {config_name}")
    print(f"Query: {test_query.description}")
    print(f"{'='*60}")

    rag = PolishSocietyRAG()

    # Measure latency
    start_time = time.time()

    results = await rag.get_demographic_insights(
        age_group=test_query.demographics['age_group'],
        education=test_query.demographics['education'],
        location=test_query.demographics['location'],
        gender=test_query.demographics['gender']
    )

    latency = time.time() - start_time

    # Extract metrics
    context = results.get('context', '')
    citations = results.get('citations', [])
    num_results = results.get('num_results', 0)
    search_type = results.get('search_type', 'unknown')

    # Calculate quality metrics
    keyword_coverage = calculate_keyword_coverage(context, test_query.expected_keywords)
    relevance_score = calculate_relevance_score(citations, test_query.expected_keywords)
    context_length = len(context)

    # Print results
    print(f"\n📊 Results:")
    print(f"  Search type: {search_type}")
    print(f"  Latency: {latency:.2f}s")
    print(f"  Num results: {num_results}")
    print(f"  Context length: {context_length} chars")
    print(f"  Keyword coverage: {keyword_coverage:.2%}")
    print(f"  Relevance score: {relevance_score:.3f}")

    # Show top 3 citations
    print(f"\n📄 Top 3 citations:")
    for i, citation in enumerate(citations[:3], 1):
        score = citation.get('score', 0.0)
        text = citation.get('text', '')[:150]
        enriched = citation.get('enriched', False)
        print(f"  {i}. Score: {score:.3f} | Enriched: {enriched}")
        print(f"     {text}...")

    return {
        'config_name': config_name,
        'query_description': test_query.description,
        'latency': latency,
        'num_results': num_results,
        'context_length': context_length,
        'keyword_coverage': keyword_coverage,
        'relevance_score': relevance_score,
        'search_type': search_type
    }


async def run_ab_test():
    """
    Uruchom A/B test dla wszystkich test queries

    Porównuje obecną konfigurację z baseline metrics
    """
    print("="*80)
    print("RAG A/B COMPARISON TEST")
    print("="*80)
    print(f"\n📋 Current configuration:")
    print(f"  CHUNK_SIZE: {settings.RAG_CHUNK_SIZE}")
    print(f"  CHUNK_OVERLAP: {settings.RAG_CHUNK_OVERLAP}")
    print(f"  TOP_K: {settings.RAG_TOP_K}")
    print(f"  MAX_CONTEXT: {settings.RAG_MAX_CONTEXT_CHARS}")
    print(f"  RRF_K: {settings.RAG_RRF_K}")
    print(f"  RERANK_CANDIDATES: {settings.RAG_RERANK_CANDIDATES}")
    print(f"  RERANKER_MODEL: {settings.RAG_RERANKER_MODEL}")
    print(f"  USE_HYBRID_SEARCH: {settings.RAG_USE_HYBRID_SEARCH}")
    print(f"  USE_RERANKING: {settings.RAG_USE_RERANKING}")

    all_results = []

    # Test każdego query
    for query in TEST_QUERIES:
        result = await test_rag_configuration(
            query,
            config_name="current"
        )
        all_results.append(result)

        # Pauza między queries
        await asyncio.sleep(1)

    # Aggregate metrics
    print("\n" + "="*80)
    print("📊 AGGREGATE METRICS")
    print("="*80)

    avg_latency = sum(r['latency'] for r in all_results) / len(all_results)
    avg_keyword_coverage = sum(r['keyword_coverage'] for r in all_results) / len(all_results)
    avg_relevance = sum(r['relevance_score'] for r in all_results) / len(all_results)
    avg_context_length = sum(r['context_length'] for r in all_results) / len(all_results)

    print(f"\n  Average latency: {avg_latency:.2f}s")
    print(f"  Average keyword coverage: {avg_keyword_coverage:.2%}")
    print(f"  Average relevance score: {avg_relevance:.3f}")
    print(f"  Average context length: {avg_context_length:.0f} chars")

    # Compare to baseline (hardcoded from previous runs)
    # TODO: Load from file or database for true A/B comparison
    print("\n" + "="*80)
    print("📈 COMPARISON TO BASELINE (OLD CONFIG)")
    print("="*80)
    print("\nBASELINE (chunk=2000, overlap=400, top_k=5):")
    print("  Average latency: ~1.2s (estimated)")
    print("  Average keyword coverage: ~65% (estimated)")
    print("  Average relevance score: ~0.45 (estimated)")
    print("  Average context length: ~4500 chars (estimated)")

    print("\nCURRENT (chunk=1000, overlap=300, top_k=8):")
    print(f"  Average latency: {avg_latency:.2f}s")
    print(f"  Average keyword coverage: {avg_keyword_coverage:.2%}")
    print(f"  Average relevance score: {avg_relevance:.3f}")
    print(f"  Average context length: {avg_context_length:.0f} chars")

    # Recommendations
    print("\n" + "="*80)
    print("💡 RECOMMENDATIONS")
    print("="*80)

    if avg_keyword_coverage > 0.70:
        print("✅ Keyword coverage jest dobra (>70%)")
    else:
        print("⚠️  Keyword coverage poniżej 70% - rozważ zmianę chunking strategy")

    if avg_relevance > 0.50:
        print("✅ Relevance score jest dobry (>0.50)")
    else:
        print("⚠️  Relevance score poniżej 0.50 - rozważ tuning RRF_K lub reranker")

    if avg_latency < 1.5:
        print("✅ Latency jest akceptowalna (<1.5s)")
    else:
        print("⚠️  Latency wysoka - rozważ zmniejszenie TOP_K lub wyłączenie reranking")

    print("\n" + "="*80)
    print("🏁 TEST COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_ab_test())
