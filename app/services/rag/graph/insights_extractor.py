"""Graph Insights Extractor - Wzbogacanie węzłów grafu i odpowiadanie na pytania.

Odpowiedzialny za:
- Wzbogacanie węzłów grafu o metadane dokumentów
- Walidację jakości danych w grafie
- Odpowiadanie na pytania z wykorzystaniem Graph RAG (kontekst grafowy + wektorowy)
"""

import logging
from typing import Any

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def enrich_graph_nodes(
    graph_documents: list[Any],
    doc_id: str,
    metadata: dict[str, Any]
) -> list[Any]:
    """Wzbogaca węzły grafu o metadane dokumentu i waliduje jakość danych.

    Args:
        graph_documents: Lista GraphDocument z LLMGraphTransformer
        doc_id: UUID dokumentu źródłowego
        metadata: Metadane dokumentu (title, country, itp.)

    Returns:
        Lista wzbogaconych GraphDocument z pełnymi metadanymi

    Proces wzbogacania:
        1. Dodaje doc_id, chunk_index do każdego węzła
        2. Dodaje metadane dokumentu: title, country, date
        3. Waliduje jakość metadanych węzłów (sprawdza czy summary i description nie są puste)
        4. Dodaje timestamp przetwarzania
        5. Normalizuje formaty danych (confidence, magnitude)
    """
    from datetime import datetime, timezone

    logger.info(
        "Wzbogacam %s dokumentów grafu o metadane doc_id=%s",
        len(graph_documents),
        doc_id
    )

    enriched_count = 0
    validation_warnings = 0

    for graph_doc in graph_documents:
        # Pobierz chunk_index z source document jeśli dostępny
        chunk_index = graph_doc.source.metadata.get("chunk_index", 0) if graph_doc.source else 0

        # Wzbogacenie węzłów
        for node in graph_doc.nodes:
            # 1. METADANE TECHNICZNE (krytyczne dla usuwania dokumentów)
            if not hasattr(node, 'properties'):
                node.properties = {}

            node.properties['doc_id'] = doc_id
            node.properties['chunk_index'] = chunk_index
            node.properties['processed_at'] = datetime.now(timezone.utc).isoformat()

            # 2. METADANE DOKUMENTU (kontekst źródłowy)
            node.properties['document_title'] = metadata.get('title', 'Unknown')
            node.properties['document_country'] = metadata.get('country', 'Poland')
            if metadata.get('date'):
                node.properties['document_year'] = str(metadata.get('date'))

            # 3. WALIDACJA JAKOŚCI METADANYCH
            # Sprawdź czy kluczowe właściwości są wypełnione
            if node.properties.get('streszczenie') in (None, '', 'N/A'):
                validation_warnings += 1
                logger.debug(
                    "Węzeł '%s' nie ma streszczenia - LLM może nie wyekstraktować wszystkich właściwości",
                    node.id
                )

            # 4. NORMALIZACJA FORMATÓW
            # Pewność normalizacja
            pewnosc = node.properties.get('pewnosc', '').lower()
            if pewnosc not in ('wysoka', 'srednia', 'niska'):
                node.properties['pewnosc'] = 'srednia'  # default

            # Skala - upewnij się że jest stringiem
            if node.properties.get('skala') and not isinstance(node.properties['skala'], str):
                node.properties['skala'] = str(node.properties['skala'])

            enriched_count += 1

        # Wzbogacenie relacji
        for relationship in graph_doc.relationships:
            if not hasattr(relationship, 'properties'):
                relationship.properties = {}

            # Metadane techniczne
            relationship.properties['doc_id'] = doc_id
            relationship.properties['chunk_index'] = chunk_index

            # Normalizacja siły (jedyna property relacji)
            sila = relationship.properties.get('sila', '').lower()
            if sila not in ('silna', 'umiarkowana', 'slaba'):
                relationship.properties['sila'] = 'umiarkowana'  # default

    logger.info(
        "Wzbogacono %s węzłów. Ostrzeżenia walidacji: %s",
        enriched_count,
        validation_warnings
    )

    if validation_warnings > enriched_count * 0.3:  # >30% węzłów bez summary
        logger.warning(
            "Wysoki odsetek węzłów (%s%%) bez pełnych metadanych. "
            "LLM może potrzebować lepszych instrukcji lub większego kontekstu.",
            int(validation_warnings / enriched_count * 100)
        )

    return graph_documents


async def answer_question(
    llm: Any,
    graph_store: Any,
    vector_store: Any,
    question: str,
    generate_cypher_fn
) -> dict[str, Any]:
    """Realizuje pełen przepływ Graph RAG i zwraca ustrukturyzowaną odpowiedź.

    Args:
        llm: LangChain LLM instance
        graph_store: Neo4j graph store instance
        vector_store: Vector store instance
        question: Pytanie użytkownika
        generate_cypher_fn: Funkcja generująca zapytanie Cypher (z graph_query_builder)

    Returns:
        Dict z odpowiedzią, kontekstem grafowym, wektorowym i zapytaniem Cypher

    Raises:
        ConnectionError: Jeśli brak dostępu do grafu lub vector store
    """
    if not graph_store or not vector_store:
        raise ConnectionError(
            "Graph RAG wymaga jednoczesnego dostępu do grafu i indeksu wektorowego."
        )

    logger.info("Generuję zapytanie Cypher dla pytania: %s", question)
    rag_query = generate_cypher_fn(llm, graph_store, question)
    logger.info("Wygenerowane zapytanie Cypher: %s", rag_query.cypher_query)

    # 1. Kontekst grafowy – zapytanie Cypher wygenerowane przez LLM.
    try:
        graph_context = graph_store.query(rag_query.cypher_query)
    except Exception as exc:  # pragma: no cover - logujemy i kontynuujemy
        logger.error("Błąd wykonania zapytania Cypher: %s", exc, exc_info=True)
        graph_context = []

    # 2. Kontekst wektorowy – semantyczne wyszukiwanie po encjach.
    vector_context_docs: list[Document] = []
    if rag_query.entities:
        search_query = " ".join(rag_query.entities)
        vector_context_docs = await vector_store.asimilarity_search(search_query, k=5)

    # 3. Agregacja kontekstu i wygenerowanie odpowiedzi końcowej.
    final_context = "KONTEKST Z GRAFU WIEDZY:\n" + str(graph_context)
    final_context += "\n\nFRAGMENTY Z DOKUMENTÓW:\n"
    for doc in vector_context_docs:
        final_context += f"- {doc.page_content}\n"

    # Pobierz prompt z config/prompts/rag/graph_rag_answer.yaml
    from config import prompts
    answer_prompt_template = prompts.get("rag.graph_rag_answer")

    # Renderuj prompt ze zmiennymi
    rendered_messages = answer_prompt_template.render(
        question=question,
        context=final_context
    )

    # Wywołaj LLM z renderowanymi wiadomościami
    response = await llm.ainvoke(rendered_messages)

    return {
        "answer": response.content,
        "graph_context": graph_context,
        "vector_context": [doc.to_json() for doc in vector_context_docs],
        "cypher_query": rag_query.cypher_query,
    }
