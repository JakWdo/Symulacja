"""Neo4j fulltext search dla hybrid RAG system.

Moduł odpowiada za:
- Lazy initialization fulltext index w Neo4j
- Wyszukiwanie pełnotekstowe z sanityzacją Lucene
- Graceful degradation (fallback do vector-only przy błędach)
"""

import asyncio
import logging
from typing import List, Tuple

from langchain_core.documents import Document
from config import rag

logger = logging.getLogger(__name__)


async def ensure_fulltext_index(vector_store) -> None:
    """Tworzy indeks fulltext w Neo4j na potrzeby wyszukiwania keywordowego.
    
    Args:
        vector_store: Neo4j vector store instance
    """
    if not vector_store:
        return

    try:
        driver = vector_store._driver

        def check_and_create_index() -> None:
            with driver.session() as session:
                def ensure(tx) -> None:
                    indexes = [record["name"] for record in tx.run("SHOW INDEXES")]
                    if "rag_fulltext_index" not in indexes:
                        tx.run(
                            """
                            CREATE FULLTEXT INDEX rag_fulltext_index IF NOT EXISTS
                            FOR (n:RAGChunk)
                            ON EACH [n.text]
                            """
                        )

                session.execute_write(ensure)

        await asyncio.to_thread(check_and_create_index)
        logger.info("Fulltext index 'rag_fulltext_index' jest gotowy.")
    except Exception as exc:  # pragma: no cover - indeks nie jest krytyczny
        logger.warning("Nie udało się utworzyć indeksu fulltext: %s", exc)


async def keyword_search(
    query: str,
    k: int,
    vector_store,
    sanitize_query_func
) -> List[Tuple[Document, float]]:
    """Wykonuje wyszukiwanie pełnotekstowe w Neo4j i zwraca dokumenty LangChain.

    Args:
        query: Search query
        k: Number of results
        vector_store: Neo4j vector store instance
        sanitize_query_func: Function to sanitize Lucene query

    Returns:
        List of (Document, score) tuples
    """
    if not vector_store:
        return []

    # SANITYZACJA: Escape znaków specjalnych Lucene przed wysłaniem query
    sanitized_query = sanitize_query_func(query)

    try:
        driver = vector_store._driver

        def search() -> List[Tuple[Document, float]]:
            session_ctx = driver.session()
            cleanup = None

            if hasattr(session_ctx, "__enter__"):
                session = session_ctx.__enter__()

                def _cleanup() -> None:
                    session_ctx.__exit__(None, None, None)

                cleanup = _cleanup
            elif hasattr(session_ctx, "__aenter__"):
                session = session_ctx.__aenter__()
                if asyncio.iscoroutine(session):
                    session = asyncio.run(session)

                def _async_cleanup():
                    result = session_ctx.__aexit__(None, None, None)
                    if asyncio.iscoroutine(result):
                        asyncio.run(result)

                cleanup = _async_cleanup
            else:
                session = session_ctx
                cleanup = getattr(session, "close", None)

            try:
                result = session.run(
                    """
                    CALL db.index.fulltext.queryNodes('rag_fulltext_index', $search_query)
                    YIELD node, score
                    RETURN node.text AS text,
                           node.doc_id AS doc_id,
                           node.title AS title,
                           node.chunk_index AS chunk_index,
                           score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    search_query=sanitized_query,
                    limit=k,
                )

                records = result.data() if hasattr(result, "data") else list(result)

                documents_with_scores: List[Tuple[Document, float]] = []
                for record in records:
                    # Obsłuż zarówno nowy format (text, doc_id, ...) jak i starszy (node -> {...})
                    if "text" in record:
                        text = record.get("text")
                        doc_id = record.get("doc_id")
                        title = record.get("title")
                        chunk_index = record.get("chunk_index")
                        score = float(record.get("score", 0.0))
                    elif "node" in record:
                        node_props = record.get("node") or {}
                        text = node_props.get("text")
                        doc_id = node_props.get("doc_id")
                        title = node_props.get("title")
                        chunk_index = node_props.get("chunk_index")
                        score = float(record.get("score", 0.0))
                    else:
                        text = None
                        doc_id = None
                        title = None
                        chunk_index = None
                        score = float(record.get("score", 0.0))

                    if not text:
                        continue

                    doc = Document(
                        page_content=text,
                        metadata={
                            "doc_id": doc_id,
                            "title": title,
                            "chunk_index": chunk_index,
                            "keyword_score": score,
                        },
                    )
                    documents_with_scores.append((doc, score))

                return documents_with_scores
            finally:
                try:
                    if cleanup:
                        cleanup()
                except Exception:  # pragma: no cover - best-effort cleanup
                    pass

        documents_with_scores = await asyncio.to_thread(search)
        logger.info("Keyword search zwróciło %s wyników", len(documents_with_scores))
        return documents_with_scores
    except Exception as exc:
        # Rozróżniamy różne typy błędów dla lepszego debugowania
        error_type = type(exc).__name__

        # Lucene query syntax errors (np. nieescapowane znaki specjalne)
        if "CypherSyntaxError" in error_type or "TokenMgrError" in str(exc):
            logger.error(
                "❌ Lucene query syntax error (prawdopodobnie znaki specjalne): %s. "
                "Query: '%s'. Falling back to vector-only search.",
                exc,
                query[:100]
            )
        # Index nie istnieje lub inne błędy konfiguracji
        elif "index" in str(exc).lower() or "fulltext" in str(exc).lower():
            logger.warning(
                "⚠️ Fulltext index niedostępny lub niepoprawnie skonfigurowany: %s. "
                "Falling back to vector-only search.",
                exc
            )
        # Inne błędy
        else:
            logger.warning(
                "⚠️ Keyword search failed (%s): %s. Falling back to vector-only search.",
                error_type,
                exc
            )

        # Zawsze zwracamy pustą listę (graceful degradation do vector-only)
        return []
