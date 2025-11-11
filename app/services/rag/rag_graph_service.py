"""Serwis Graph RAG - budowa i zapytania grafu wiedzy.

Ten moduł został podzielony na 3 moduły (Prompt 6):
- graph_query_builder.py: Generowanie zapytań Cypher
- graph_traversal.py: Przechodzenie grafu, cache, wykonywanie zapytań
- graph_insights_extractor.py: Wzbogacanie węzłów, answer_question

Ten wrapper zachowuje backward compatibility dla istniejących importów.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.shared.clients import build_chat_model
from app.services.rag.rag_clients import get_graph_store, get_vector_store

# Import modułów
from app.services.rag.graph_query_builder import generate_cypher_query
from app.services.rag.graph_traversal import GraphTraversal
from app.services.rag.graph_insights_extractor import (
    enrich_graph_nodes,
    answer_question as answer_question_impl
)

logger = logging.getLogger(__name__)


class GraphRAGService:
    """Serwis zarządzający grafem wiedzy i zapytaniami Graph RAG.

    Zakres odpowiedzialności:

    1. Wzbogacanie węzłów grafu o metadane dokumentów
    2. Generowanie zapytań Cypher na podstawie pytań użytkownika
    3. Odpowiadanie na pytania z wykorzystaniem Graph RAG (połączenie kontekstu
       grafowego i semantycznego)
    4. Pobieranie kontekstu demograficznego z grafu wiedzy

    Uwaga: Podstawowa infrastruktura dokumentów (load, chunk, vector) znajduje się
    w RAGDocumentService.
    """

    def __init__(self) -> None:
        """Inicjalizuje komponenty Graph RAG."""

        from config import models

        # Model config z centralnego registry
        model_config = models.get("rag", "graph")
        self.llm = build_chat_model(**model_config.params)

        # Połączenia do Neo4j
        self.graph_store = get_graph_store(logger)
        self.vector_store = get_vector_store(logger)

        # GraphTraversal instance (dla cache i demographic context)
        self.traversal = GraphTraversal(self.graph_store) if self.graph_store else None

    @staticmethod
    def enrich_graph_nodes(
        graph_documents: list[Any],
        doc_id: str,
        metadata: dict[str, Any]
    ) -> list[Any]:
        """Wzbogaca węzły grafu o metadane dokumentu (deleguje do graph_insights_extractor)."""
        return enrich_graph_nodes(graph_documents, doc_id, metadata)

    # Backwards compatibility (tests + starsze moduły)
    @staticmethod
    def _enrich_graph_nodes(
        graph_documents: list[Any],
        doc_id: str,
        metadata: dict[str, Any]
    ) -> list[Any]:
        """Backward compatibility wrapper."""
        return enrich_graph_nodes(graph_documents, doc_id, metadata)

    def _generate_cypher_query(self, question: str):
        """Generuje zapytanie Cypher (deleguje do graph_query_builder)."""
        return generate_cypher_query(self.llm, self.graph_store, question)

    async def answer_question(self, question: str) -> dict[str, Any]:
        """Odpowiada na pytanie (deleguje do graph_insights_extractor)."""
        return await answer_question_impl(
            self.llm,
            self.graph_store,
            self.vector_store,
            question,
            self._generate_cypher_query
        )

    @staticmethod
    def _normalize_education_term(education: str) -> list[str]:
        """Normalizuje education term (deleguje do GraphTraversal)."""
        return GraphTraversal.normalize_education_term(education)

    async def get_demographic_graph_context(
        self,
        age_group: str,
        location: str,
        education: str,
        gender: str
    ) -> list[dict[str, Any]]:
        """Pobiera kontekst demograficzny (deleguje do GraphTraversal)."""
        if not self.traversal:
            logger.warning("GraphTraversal nie jest dostępne - graph_store is None")
            return []

        return await self.traversal.get_demographic_graph_context(
            age_group, location, education, gender
        )
