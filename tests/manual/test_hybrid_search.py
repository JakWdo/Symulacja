#!/usr/bin/env python3
"""
Test script dla RAG Hybrid Search

Demonstracja działania hybrid search (vector + keyword + RRF fusion)
w systemie RAG dla generowania person.

Uruchomienie:
    python scripts/test_hybrid_search.py
"""

import asyncio
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.manual

# Dodaj root directory do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag.rag_hybrid_search_service import PolishSocietyRAG
from app.core.config import get_settings

settings = get_settings()


async def test_hybrid_search():
    """
    Test hybrid search z przykładowym query demograficznym
    """
    print("=" * 80)
    print("RAG HYBRID SEARCH TEST")
    print("=" * 80)
    print()

    # Inicjalizuj RAG service
    print("Inicjalizacja PolishSocietyRAG...")
    rag = PolishSocietyRAG()

    if not rag.vector_store:
        print("❌ ERROR: Neo4j Vector Store nie jest dostępny!")
        print("Upewnij się że:")
        print("  1. Neo4j jest uruchomiony (docker-compose up neo4j)")
        print("  2. GOOGLE_API_KEY jest ustawiony w .env")
        print("  3. Dokumenty RAG zostały zaindeksowane")
        return

    print("✅ PolishSocietyRAG zainicjalizowany")
    print()

    # Upewnij się że fulltext index istnieje
    print("Tworzenie fulltext index (jeśli nie istnieje)...")
    await rag._ensure_fulltext_index()
    print("✅ Fulltext index gotowy")
    print()

    # Test query - profil demograficzny
    print("=" * 80)
    print("TEST QUERY")
    print("=" * 80)

    age_group = "25-34"
    education = "Wyższe magisterskie"
    location = "Warszawa"
    gender = "kobieta"

    print(f"Profil demograficzny:")
    print(f"  • Wiek: {age_group}")
    print(f"  • Wykształcenie: {education}")
    print(f"  • Lokalizacja: {location}")
    print(f"  • Płeć: {gender}")
    print()

    # Wykonaj hybrid search
    print("Wykonywanie hybrid search (vector + keyword + RRF)...")
    print()

    result = await rag.get_demographic_insights(
        age_group=age_group,
        education=education,
        location=location,
        gender=gender
    )

    # Wyświetl wyniki
    print("=" * 80)
    print("WYNIKI")
    print("=" * 80)
    print()

    print(f"Search type: {result.get('search_type', 'unknown')}")
    print(f"Liczba wyników (hybrid search): {result['num_results']}")
    print(f"Liczba węzłów grafu: {len(result.get('graph_nodes', []))}")
    print(f"Długość kontekstu: {len(result['context'])} znaków")
    print(f"Długość graph context: {len(result.get('graph_context', ''))} znaków")
    print(f"Liczba citations: {len(result['citations'])}")
    print()

    # Wyświetl graph nodes jeśli są
    if result.get('graph_nodes'):
        print("=" * 80)
        print("WĘZŁY GRAFU (Graph Context)")
        print("=" * 80)
        print()

        graph_nodes = result['graph_nodes']
        for i, node in enumerate(graph_nodes, 1):
            print(f"--- Węzeł #{i} ({node.get('type', 'Unknown')}) ---")
            print(f"Summary: {node.get('summary', 'N/A')}")

            if node.get('magnitude'):
                print(f"Wielkość: {node['magnitude']}")
            if node.get('time_period'):
                print(f"Okres: {node['time_period']}")
            if node.get('confidence_level'):
                print(f"Pewność: {node['confidence_level']}")
            if node.get('key_facts'):
                print(f"Kluczowe fakty: {node['key_facts']}")

            print()
    else:
        print("ℹ️  Brak wyników z grafu - dokument może nie mieć Graph RAG nodes lub graf jest pusty")
        print()

    # Wyświetl top 3 citations
    if result['citations']:
        print("=" * 80)
        print("TOP 3 CITATIONS (z scores)")
        print("=" * 80)
        print()

        for i, citation in enumerate(result['citations'][:3], 1):
            print(f"--- Citation #{i} (score: {citation['score']:.4f}) ---")
            print(f"Źródło: {citation['metadata'].get('title', 'Unknown')}")
            print(f"Chunk: {citation['metadata'].get('chunk_index', '?')}")
            print()
            # Wyświetl pierwsze 200 znaków
            text = citation['text']
            preview = text[:200] + "..." if len(text) > 200 else text
            print(preview)
            print()

    # Wyświetl fragment kontekstu
    if result['context']:
        print("=" * 80)
        print("FRAGMENT KONTEKSTU (pierwsze 500 znaków)")
        print("=" * 80)
        print()
        preview = result['context'][:500] + "..." if len(result['context']) > 500 else result['context']
        print(preview)
        print()

    print("=" * 80)
    print("TEST ZAKOŃCZONY")
    print("=" * 80)
    print()

    # Porównanie z vector-only
    if settings.RAG_USE_HYBRID_SEARCH:
        print("💡 TIP: Aby porównać z vector-only search, ustaw:")
        print("   RAG_USE_HYBRID_SEARCH=False w config.py")
        print()


if __name__ == "__main__":
    asyncio.run(test_hybrid_search())
