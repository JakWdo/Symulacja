"""
Pomocnicze funkcje do zarządzania połączeniami z Neo4j dla usług RAG.

Zapewnia:
- współdzielony dostęp do Neo4jVector oraz Neo4jGraph
- retry logic z wykładniczym backoffem
- spójne logowanie
"""

from __future__ import annotations

import logging
import time
from typing import TypeVar
from collections.abc import Callable

from langchain_neo4j import Neo4jGraph, Neo4jVector

from app.core.config import get_settings
from app.services.shared.clients import get_embeddings

settings = get_settings()

T = TypeVar("T")

_VECTOR_STORE: Neo4jVector | None = None
_GRAPH_STORE: Neo4jGraph | None = None


def _connect_with_retry(
    factory: Callable[[], T],
    logger: logging.Logger,
    description: str,
    max_retries: int = 10,
    initial_delay: float = 1.0,
) -> T | None:
    """Ogólny mechanizm retry dla połączeń z Neo4j."""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            resource = factory()
            logger.info("✅ %s połączony (próba %d/%d)", description, attempt, max_retries)
            return resource
        except Exception as exc:  # pragma: no cover - zależne od środowiska Neo4j
            if attempt >= max_retries:
                logger.error(
                    "❌ %s - wszystkie %d próby zakończone niepowodzeniem: %s",
                    description,
                    max_retries,
                    exc,
                    exc_info=True,
                )
                return None

            logger.warning(
                "⚠️  %s - próba %d/%d nieudana: %s. Ponowna próba za %.1fs...",
                description,
                attempt,
                max_retries,
                str(exc)[:100],
                delay,
            )
            time.sleep(delay)
            delay = min(delay * 1.5, 10.0)

    return None


def get_vector_store(logger: logging.Logger) -> Neo4jVector | None:
    """Zwraca (cache'owaną) instancję Neo4jVector z retry logic."""
    global _VECTOR_STORE
    if _VECTOR_STORE is None:
        embeddings = get_embeddings()
        _VECTOR_STORE = _connect_with_retry(
            lambda: Neo4jVector(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
                embedding=embeddings,
                index_name="rag_document_embeddings",
                node_label="RAGChunk",
                text_node_property="text",
                embedding_node_property="embedding",
            ),
            logger,
            "Neo4j Vector Store",
        )
    return _VECTOR_STORE


def get_graph_store(logger: logging.Logger) -> Neo4jGraph | None:
    """Zwraca (cache'owaną) instancję Neo4jGraph z retry logic."""
    global _GRAPH_STORE
    if _GRAPH_STORE is None:
        _GRAPH_STORE = _connect_with_retry(
            lambda: Neo4jGraph(
                url=settings.NEO4J_URI,
                username=settings.NEO4J_USER,
                password=settings.NEO4J_PASSWORD,
            ),
            logger,
            "Neo4j Graph Store",
        )
    return _GRAPH_STORE
