"""
Tuning parametru RRF_K dla hybrydowego wyszukiwania
===================================================

Skrypt testuje wpływ różnych wartości RRF_K (40, 60, 80) na jakość fuzji
vector search i keyword search.

RRF (Reciprocal Rank Fusion) formula:
    score = 1 / (k + rank)

Gdzie:
- k=40 (elitarne) - większy wpływ top results z każdej metody
- k=60 (standardowe) - balans
- k=80 (demokratyczne) - mniejsze różnice między rankings

Użycie:
    python tests/manual/test_rrf_k_tuning.py

Wymaga:
    - Uruchomiony Neo4j z zaindeksowanymi dokumentami
    - GOOGLE_API_KEY w .env
"""

import asyncio
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from langchain_core.documents import Document

from app.services.rag_service import PolishSocietyRAG
from app.core.config import get_settings

settings = get_settings()


@dataclass
class RRFKTestCase:
    """Test case dla konkretnej wartości k"""
    k_value: int
    description: str


# Test różnych wartości k
RRF_K_VALUES = [
    RRFKTestCase(k_value=40, description="Elitarne (favoryzuje top results)"),
    RRFKTestCase(k_value=60, description="Standardowe (balans)"),
    RRFKTestCase(k_value=80, description="Demokratyczne (równomierne)")
]


def analyze_rrf_distribution(
    fused_results: List[Tuple[Document, float]]
) -> Dict[str, Any]:
    """
    Analizuj dystrybucję scores w RRF fusion results

    Args:
        fused_results: Lista (Document, RRF_score) par

    Returns:
        Dict z metrykami dystrybucji
    """
    if not fused_results:
        return {
            'num_results': 0,
            'top_score': 0.0,
            'bottom_score': 0.0,
            'score_range': 0.0,
            'avg_score': 0.0,
            'score_std': 0.0
        }

    scores = [score for _, score in fused_results]

    import statistics

    return {
        'num_results': len(scores),
        'top_score': max(scores),
        'bottom_score': min(scores),
        'score_range': max(scores) - min(scores),
        'avg_score': statistics.mean(scores),
        'score_std': statistics.stdev(scores) if len(scores) > 1 else 0.0
    }


async def test_rrf_k_value(
    k_value: int,
    query: str
) -> Dict[str, Any]:
    """
    Test konkretnej wartości RRF_K

    Args:
        k_value: Wartość parametru k
        query: Query do przetestowania

    Returns:
        Dict z metrics i results
    """
    print(f"\n{'='*60}")
    print(f"Testing RRF_K = {k_value}")
    print(f"{'='*60}")

    rag = PolishSocietyRAG()

    # HACK: Tymczasowo nadpisz settings.RAG_RRF_K
    # W production stworzysz instancję PolishSocietyRAG z custom settings
    original_k = settings.RAG_RRF_K
    settings.RAG_RRF_K = k_value

    start_time = time.time()

    # Wykonaj hybrid search (z custom k)
    # Niestety nie mamy bezpośredniego dostępu do _rrf_fusion z zewnątrz
    # Więc użyjemy get_demographic_insights i przeanalizujemy results
    results = await rag.get_demographic_insights(
        age_group="25-34",
        education="wyższe",
        location="Warszawa",
        gender="kobieta"
    )

    latency = time.time() - start_time

    # Restore original k
    settings.RAG_RRF_K = original_k

    # Analyze citations (które już mają RRF scores)
    citations = results.get('citations', [])

    if not citations:
        print("⚠️  Brak citations - możliwe że hybrid search nie działa")
        return {
            'k_value': k_value,
            'latency': latency,
            'num_results': 0
        }

    # Extract scores
    scores = [c.get('score', 0.0) for c in citations]

    import statistics

    metrics = {
        'k_value': k_value,
        'latency': latency,
        'num_results': len(citations),
        'top_score': max(scores) if scores else 0.0,
        'bottom_score': min(scores) if scores else 0.0,
        'score_range': max(scores) - min(scores) if scores else 0.0,
        'avg_score': statistics.mean(scores) if scores else 0.0,
        'score_std': statistics.stdev(scores) if len(scores) > 1 else 0.0
    }

    # Print results
    print(f"\n📊 Metrics:")
    print(f"  Latency: {latency:.2f}s")
    print(f"  Num results: {metrics['num_results']}")
    print(f"  Top score: {metrics['top_score']:.4f}")
    print(f"  Bottom score: {metrics['bottom_score']:.4f}")
    print(f"  Score range: {metrics['score_range']:.4f}")
    print(f"  Average score: {metrics['avg_score']:.4f}")
    print(f"  Score std dev: {metrics['score_std']:.4f}")

    # Show top 3 results
    print(f"\n📄 Top 3 results:")
    for i, citation in enumerate(citations[:3], 1):
        score = citation.get('score', 0.0)
        text = citation.get('text', '')[:100]
        print(f"  {i}. Score: {score:.4f}")
        print(f"     {text}...")

    return metrics


async def run_rrf_k_tuning():
    """
    Uruchom tuning dla różnych wartości RRF_K

    Porównuje k=40, 60, 80 na tym samym query
    """
    print("="*80)
    print("RRF_K TUNING TEST")
    print("="*80)
    print(f"\nCurrent RRF_K: {settings.RAG_RRF_K}")
    print(f"Testing values: 40, 60, 80")

    test_query = (
        "Profil demograficzny: kobieta, wiek 25-34, wykształcenie wyższe, "
        "lokalizacja Warszawa w Polsce"
    )

    print(f"\nTest query: {test_query}")

    all_results = []

    # Test każdej wartości k
    for test_case in RRF_K_VALUES:
        print(f"\n{test_case.description}")

        result = await test_rrf_k_value(
            k_value=test_case.k_value,
            query=test_query
        )
        all_results.append(result)

        # Pauza
        await asyncio.sleep(0.5)

    # Compare all results
    print("\n" + "="*80)
    print("📊 COMPARISON")
    print("="*80)

    print("\n{:<10} {:<15} {:<15} {:<15} {:<15}".format(
        "RRF_K", "Avg Score", "Score Range", "Std Dev", "Latency"
    ))
    print("-" * 80)

    for result in all_results:
        print("{:<10} {:<15.4f} {:<15.4f} {:<15.4f} {:<15.2f}s".format(
            result['k_value'],
            result['avg_score'],
            result['score_range'],
            result['score_std'],
            result['latency']
        ))

    # Recommendations
    print("\n" + "="*80)
    print("💡 INTERPRETATION")
    print("="*80)

    print("\n📈 Score Range:")
    print("  - Większy range = większe różnice między top/bottom results")
    print("  - Przydatne jeśli chcesz wyraźnie odróżnić best matches")

    print("\n📊 Standard Deviation:")
    print("  - Wyższa std = większa różnorodność scores")
    print("  - Niższa std = bardziej równomierne scores")

    print("\n⚡ Latency:")
    print("  - Powinno być podobne dla wszystkich k (fusion jest szybka)")
    print("  - Jeśli różnice >10%, może być issue z timing")

    print("\n" + "="*80)
    print("🎯 RECOMMENDATION")
    print("="*80)

    # Find best k based on score range (chcemy większy range dla lepszej precyzji)
    best_k_result = max(all_results, key=lambda r: r['score_range'])
    print(f"\n✅ Zalecane RRF_K: {best_k_result['k_value']}")
    print(f"   Uzasadnienie: Największy score range ({best_k_result['score_range']:.4f})")
    print(f"   Co oznacza lepszą separację top results od bottom results")

    print("\n💡 Note:")
    print("   RRF_K to hyperparameter - ostateczny wybór zależy od:")
    print("   - Charakterystyki datasetu")
    print("   - Preferencji użytkownika (precision vs recall)")
    print("   - A/B testów na produkcyjnych queries")

    print("\n" + "="*80)
    print("🏁 TUNING COMPLETED")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(run_rrf_k_tuning())
