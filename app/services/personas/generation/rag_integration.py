"""
Moduł do integracji z RAG (Retrieval-Augmented Generation) dla person

Zawiera logikę do:
- Pobierania kontekstu z RAG dla profili demograficznych
- Budowania zapytań RAG z profili
- Cache'owania zapytań RAG w pamięci
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def get_rag_context_for_persona(
    demographic: dict[str, Any],
    rag_service,
    rag_cache: dict[tuple[str, str, str, str], dict[str, Any]]
) -> dict[str, Any] | None:
    """
    Pobierz kontekst z RAG dla danego profilu demograficznego (z cache)

    Args:
        demographic: Profil demograficzny persony
        rag_service: Instancja RAG service (singleton)
        rag_cache: In-memory cache dict (key: tuple demographics, value: dict RAG context)

    Returns:
        Dict z kluczami: context (str), citations (list), query (str),
        graph_context (str), graph_nodes (list), search_type (str)
        lub None jeśli RAG niedostępny
    """
    if not rag_service:
        return None

    # Przygotuj cache key (normalizuj wartości)
    age_group = demographic.get('age_group', '25-34')
    education = demographic.get('education_level', 'wyższe')
    location = demographic.get('location', 'Warszawa')
    gender = demographic.get('gender', 'mężczyzna')

    cache_key = (age_group, education, location, gender)

    # Sprawdź cache przed wywołaniem RAG
    if cache_key in rag_cache:
        logger.debug(
            f"RAG cache HIT dla profilu: wiek={age_group}, edukacja={education}, "
            f"lokalizacja={location}, płeć={gender}"
        )
        return rag_cache[cache_key]

    logger.debug(
        f"RAG cache MISS dla profilu: wiek={age_group}, edukacja={education}, "
        f"lokalizacja={location}, płeć={gender}"
    )

    try:
        context_data = await rag_service.get_demographic_insights(
            age_group=age_group,
            education=education,
            location=location,
            gender=gender
        )

        # Zapisz w cache dla przyszłych wywołań
        rag_cache[cache_key] = context_data

        # Loguj szczegóły RAG context
        context_len = len(context_data.get('context', ''))
        graph_nodes_count = len(context_data.get('graph_nodes', []))
        search_type = context_data.get('search_type', 'unknown')
        citations_count = len(context_data.get('citations', []))

        logger.info(
            f"RAG context retrieved: {context_len} chars, "
            f"{graph_nodes_count} graph nodes, "
            f"{citations_count} citations, "
            f"search_type={search_type}"
        )

        # Jeśli mamy graph nodes, loguj ich typy
        if graph_nodes_count > 0:
            node_types = [node.get('type', 'Unknown') for node in context_data.get('graph_nodes', [])]
            logger.info(f"Graph node types: {', '.join(node_types)}")

        return context_data
    except Exception as e:
        logger.error(f"RAG context retrieval failed: {e}", exc_info=True)
        return None


def _build_rag_query(demographic_profile: Dict[str, Any]) -> str:
    """
    Zbuduj zapytanie RAG na podstawie profilu demograficznego

    Args:
        demographic_profile: Profil demograficzny persony

    Returns:
        Query string gotowe do użycia w RAG service
    """
    age_group = demographic_profile.get('age_group', '25-34')
    education = demographic_profile.get('education_level', 'wyższe')
    location = demographic_profile.get('location', 'Warszawa')
    gender = demographic_profile.get('gender', 'mężczyzna')

    # Buduj query ze szczegółami demograficznymi
    query = (
        f"Informacje demograficzne dla osób w wieku {age_group}, "
        f"płeć: {gender}, wykształcenie: {education}, lokalizacja: {location}"
    )

    return query


def _cache_rag_query(
    query: str,
    result: str,
    cache: Dict[str, str]
) -> None:
    """
    Zapisz wynik zapytania RAG w cache

    Args:
        query: Query string
        result: Result string z RAG
        cache: Cache dict (query -> result)
    """
    cache[query] = result
    logger.debug(f"RAG query cached: {query[:100]}... -> {len(result)} chars")
