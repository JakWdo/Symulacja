"""
Archived schemas for the Graph RAG endpoint.
"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class GraphRAGQuestionRequest(BaseModel):
    """User query targeting the Graph RAG pipeline."""

    question: str = Field(
        ...,
        min_length=1,
        description="Pytanie analityczne oparte o graf wiedzy.",
    )


class GraphRAGQuestionResponse(BaseModel):
    """Structured Graph RAG answer with contextual artifacts."""

    answer: str
    graph_context: List[Dict[str, Any]]
    vector_context: List[Any]
    cypher_query: str
