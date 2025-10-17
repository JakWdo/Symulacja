"""
Archived Graph RAG endpoint implementation.

Original route:
    POST /rag/query/graph

The frontend no longer exposes this functionality, but the code is retained so
we can resurrect the feature without rewriting the integration.
"""

import logging
from typing import Any

from fastapi import Depends, HTTPException

from app.api.dependencies import get_current_user
from app.models import User
from app.schemas.archived.rag_graph import (
    GraphRAGQuestionRequest,
    GraphRAGQuestionResponse,
)
from app.services.rag.rag_graph_service import GraphRAGService

logger = logging.getLogger(__name__)

_graph_rag_service: GraphRAGService | None = None


def get_graph_rag_service() -> GraphRAGService:
    """Return a cached GraphRAGService instance."""

    global _graph_rag_service
    if _graph_rag_service is None:
        _graph_rag_service = GraphRAGService()
    return _graph_rag_service


async def query_graph_rag(
    request: GraphRAGQuestionRequest,
    current_user: User = Depends(get_current_user),
) -> GraphRAGQuestionResponse:
    """
    Archived Graph RAG endpoint.

    Raises:
        HTTPException: If Graph RAG query execution fails.
    """

    service = get_graph_rag_service()
    try:
        result: dict[str, Any] = await service.answer_question(request.question)
        return GraphRAGQuestionResponse(**result)
    except Exception as exc:  # pragma: no cover - legacy feature
        logger.error("Graph RAG query failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Nie udało się uzyskać odpowiedzi Graph RAG.",
        ) from exc
