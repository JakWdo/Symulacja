+37
-59

"""Schematy Pydantic wykorzystywane przez API RAG oraz Graph RAG."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RAGDocumentResponse(BaseModel):
    """Model odpowiedzi opisujący dokument przechowywany w bazie wiedzy."""

    id: UUID
    title: str
    filename: str
    file_path: str
    file_type: str
    country: Optional[str] = None
    num_chunks: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class RAGQueryRequest(BaseModel):
    """Schemat zapytania deweloperskiego do klasycznego RAG."""

    query: str = Field(..., min_length=1, description="Zapytanie tekstowe użytkownika.")
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Liczba wyników do zwrócenia w klasycznym wyszukiwaniu wektorowym.",
    )


class RAGCitation(BaseModel):
    """Cytowanie pojedynczego fragmentu zwróconego przez wyszukiwanie RAG."""

    document_title: str = Field(..., description="Tytuł dokumentu źródłowego.")
    chunk_text: str = Field(..., description="Treść fragmentu wykorzystanego w odpowiedzi.")
    relevance_score: float = Field(..., description="Ocena trafności (0-1).")


class RAGQueryResponse(BaseModel):
    """Ustrukturyzowana odpowiedź z klasycznego zapytania RAG."""

    query: str
    context: str
    citations: List[RAGCitation]
    num_results: int


class GraphRAGQuestionRequest(BaseModel):
    """Schemat zapytania użytkownika do zaawansowanego Graph RAG."""

    question: str = Field(
        ...,
        min_length=1,
        description="Pytanie analityczne, które ma zostać rozpatrzone w oparciu o graf wiedzy.",
        example="Jak zmieniało się zaufanie do rządu wśród młodych Polaków?",
    )


class GraphRAGQuestionResponse(BaseModel):
    """Odpowiedź Graph RAG obejmująca wynik, kontekst i zapytanie Cypher."""

    answer: str
    graph_context: List[Dict[str, Any]]
    vector_context: List[Any]
    cypher_query: str