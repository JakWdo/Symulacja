"""Graph enrichment dla hybrid search results.

Moduł odpowiada za:
- Formatowanie graph nodes do czytelnego kontekstu dla LLM
- Znajdowanie graph nodes powiązanych z chunkami
- Wzbogacanie chunków o powiązane graph nodes
"""

import inspect
import logging
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def format_graph_context(graph_nodes: list[dict[str, Any]]) -> str:
    """Formatuje węzły grafu do czytelnego kontekstu tekstowego dla LLM.

    Args:
        graph_nodes: Lista węzłów z grafu z właściwościami

    Returns:
        Sformatowany string z strukturalną wiedzą z grafu
    """
    # DEFENSIVE CHECK: Validate input type
    if inspect.iscoroutine(graph_nodes):
        logger.error(
            "❌ BUG: format_graph_context received a coroutine instead of list! "
            "This indicates a serious bug in the call chain. Cleaning up and returning empty string."
        )
        graph_nodes.close()
        return ""

    if not isinstance(graph_nodes, list):
        logger.error(
            "❌ BUG: format_graph_context received %s instead of list! "
            "Returning empty string to prevent crash",
            type(graph_nodes).__name__
        )
        return ""

    if not graph_nodes:
        return ""

    # Grupuj węzły po typie
    indicators = [n for n in graph_nodes if n.get('type') == 'Wskaznik']
    observations = [n for n in graph_nodes if n.get('type') == 'Obserwacja']
    trends = [n for n in graph_nodes if n.get('type') == 'Trend']
    demographics = [n for n in graph_nodes if n.get('type') == 'Demografia']

    sections = []

    # Sekcja Wskaźniki
    if indicators:
        sections.append("📊 WSKAŹNIKI DEMOGRAFICZNE (Wskaznik):\n")
        for ind in indicators:
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = ind.get('streszczenie') or ind.get('summary', 'Brak podsumowania')
            skala = ind.get('skala') or ind.get('magnitude', 'N/A')
            pewnosc = ind.get('pewnosc') or ind.get('confidence_level', 'N/A')
            kluczowe_fakty = ind.get('kluczowe_fakty') or ind.get('key_facts', '')
            okres_czasu = ind.get('okres_czasu') or ind.get('time_period', '')

            sections.append(f"• {streszczenie}")
            if skala and skala != 'N/A':
                sections.append(f"  Wielkość: {skala}")
            if okres_czasu:
                sections.append(f"  Okres: {okres_czasu}")
            sections.append(f"  Pewność: {pewnosc}")
            if kluczowe_fakty:
                sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
            sections.append("")

    # Sekcja Obserwacje
    if observations:
        sections.append("\n👥 OBSERWACJE DEMOGRAFICZNE (Obserwacja):\n")
        for obs in observations:
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = obs.get('streszczenie') or obs.get('summary', 'Brak podsumowania')
            pewnosc = obs.get('pewnosc') or obs.get('confidence_level', 'N/A')
            kluczowe_fakty = obs.get('kluczowe_fakty') or obs.get('key_facts', '')
            okres_czasu = obs.get('okres_czasu') or obs.get('time_period', '')

            sections.append(f"• {streszczenie}")
            sections.append(f"  Pewność: {pewnosc}")
            if okres_czasu:
                sections.append(f"  Okres: {okres_czasu}")
            if kluczowe_fakty:
                sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
            sections.append("")

    # Sekcja Trendy
    if trends:
        sections.append("\n📈 TRENDY DEMOGRAFICZNE (Trend):\n")
        for trend in trends:
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = trend.get('streszczenie') or trend.get('summary', 'Brak podsumowania')
            okres_czasu = trend.get('okres_czasu') or trend.get('time_period', 'N/A')
            kluczowe_fakty = trend.get('kluczowe_fakty') or trend.get('key_facts', '')

            sections.append(f"• {streszczenie}")
            sections.append(f"  Okres: {okres_czasu}")
            if kluczowe_fakty:
                sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
            sections.append("")

    # Sekcja Demografia
    if demographics:
        sections.append("\n🎯 GRUPY DEMOGRAFICZNE (Demografia):\n")
        for demo in demographics:
            # Backward compatibility: używaj nowych nazw z fallbackiem na stare
            streszczenie = demo.get('streszczenie') or demo.get('summary', 'Brak podsumowania')
            pewnosc = demo.get('pewnosc') or demo.get('confidence_level', 'N/A')
            kluczowe_fakty = demo.get('kluczowe_fakty') or demo.get('key_facts', '')

            sections.append(f"• {streszczenie}")
            sections.append(f"  Pewność: {pewnosc}")
            if kluczowe_fakty:
                sections.append(f"  Kluczowe fakty: {kluczowe_fakty}")
            sections.append("")

    return "\n".join(sections)


def find_related_graph_nodes(
    chunk_doc: Document,
    graph_nodes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
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
    related_nodes: list[dict[str, Any]]
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
