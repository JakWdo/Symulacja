"""Formatowanie węzłów grafu Neo4j do kontekstu tekstowego dla LLM.

Moduł grupuje węzły po typie (Wskaznik, Obserwacja, Trend, Demografia) i formatuje
je do czytelnego formatu z ikonami i backward compatibility dla starych nazw pól.
"""

import inspect
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def format_graph_context(graph_nodes: List[Dict[str, Any]]) -> str:
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
