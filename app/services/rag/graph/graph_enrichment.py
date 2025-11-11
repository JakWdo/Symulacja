"""Wzbogacanie chunków o kontekst z grafu Neo4j.

Moduł odpowiada za:
- Znajdowanie graph nodes powiązanych z chunkiem (matching via keywords/doc_id)
- Wzbogacanie tekstu chunku o powiązane wskaźniki, obserwacje i trendy
"""

import inspect
import logging
from typing import List, Dict, Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def find_related_graph_nodes(
    chunk_doc: Document,
    graph_nodes: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Znajdź graph nodes które są powiązane z danym chunkiem.

    Matching bazuje na:
    1. Wspólnych słowach kluczowych (z summary/key_facts)
    2. Dokumencie źródłowym (doc_id)

    Args:
        chunk_doc: Document chunk z vector/keyword search
        graph_nodes: Lista graph nodes z get_demographic_graph_context()

    Returns:
        Lista graph nodes które są powiązane z chunkiem
    """
    # DEFENSIVE CHECK: Validate input type
    if inspect.iscoroutine(graph_nodes):
        logger.error(
            "❌ BUG: find_related_graph_nodes received a coroutine instead of list! "
            "Cleaning up and returning empty list."
        )
        graph_nodes.close()
        return []

    if not isinstance(graph_nodes, list):
        logger.error(
            "❌ BUG: find_related_graph_nodes received %s instead of list!",
            type(graph_nodes).__name__
        )
        return []

    if not graph_nodes:
        return []

    related = []
    chunk_text = chunk_doc.page_content.lower()
    chunk_doc_id = chunk_doc.metadata.get('doc_id', '')

    for node in graph_nodes:
        # Sprawdź czy node pochodzi z tego samego dokumentu
        node_doc_id = node.get('doc_id', '')
        if node_doc_id and node_doc_id == chunk_doc_id:
            related.append(node)
            continue

        # Sprawdź overlap słów kluczowych
        # Backward compatibility: używaj nowych nazw z fallbackiem na stare
        summary = (node.get('streszczenie') or node.get('summary', '') or '').lower()
        key_facts = (node.get('kluczowe_fakty') or node.get('key_facts', '') or '').lower()

        # Ekstraktuj słowa kluczowe (> 5 chars)
        summary_words = {w for w in summary.split() if len(w) > 5}
        key_facts_words = {w for w in key_facts.split() if len(w) > 5}
        node_keywords = summary_words | key_facts_words

        # Policz overlap
        matches = sum(1 for keyword in node_keywords if keyword in chunk_text)

        # Jeśli >=2 matching keywords, uznaj za related
        if matches >= 2:
            related.append(node)

    return related


def enrich_chunk_with_graph(
    chunk_text: str,
    related_nodes: List[Dict[str, Any]]
) -> str:
    """Wzbogać chunk o powiązane graph nodes w naturalny sposób.

    Args:
        chunk_text: Oryginalny tekst chunku
        related_nodes: Powiązane graph nodes

    Returns:
        Enriched chunk text z embedded graph context
    """
    if not related_nodes:
        return chunk_text

    # Grupuj nodes po typie
    indicators = [n for n in related_nodes if n.get('type') == 'Wskaznik']
    observations = [n for n in related_nodes if n.get('type') == 'Obserwacja']
    trends = [n for n in related_nodes if n.get('type') == 'Trend']

    enrichments = []

    # Dodaj wskaźniki
    if indicators:
        enrichments.append("\n💡 Powiązane wskaźniki:")
        for ind in indicators[:2]:  # Max 2 na chunk
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = ind.get('streszczenie') or ind.get('summary', '')
            skala = ind.get('skala') or ind.get('magnitude', '')
            if streszczenie:
                if skala:
                    enrichments.append(f"  • {streszczenie} ({skala})")
                else:
                    enrichments.append(f"  • {streszczenie}")

    # Dodaj obserwacje
    if observations:
        enrichments.append("\n🔍 Powiązane obserwacje:")
        for obs in observations[:2]:  # Max 2 na chunk
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = obs.get('streszczenie') or obs.get('summary', '')
            if streszczenie:
                enrichments.append(f"  • {streszczenie}")

    # Dodaj trendy
    if trends:
        enrichments.append("\n📈 Powiązane trendy:")
        for trend in trends[:1]:  # Max 1 na chunk
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = trend.get('streszczenie') or trend.get('summary', '')
            okres_czasu = trend.get('okres_czasu') or trend.get('time_period', '')
            if streszczenie:
                if okres_czasu:
                    enrichments.append(f"  • {streszczenie} ({okres_czasu})")
                else:
                    enrichments.append(f"  • {streszczenie}")

    if enrichments:
        return chunk_text + "\n" + "\n".join(enrichments)
    else:
        return chunk_text
