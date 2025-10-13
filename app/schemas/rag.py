"""
Schematy Pydantic dla API RAG (Retrieval-Augmented Generation)

Definiują strukturę requestów i responses dla endpointów RAG.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID


class RAGDocumentResponse(BaseModel):
    """
    Response schema dla dokumentu RAG

    Zwracane przy listowaniu dokumentów i po uploadzie.
    """
    id: UUID
    title: str
    filename: str
    file_type: str  # 'pdf' lub 'docx'
    country: Optional[str] = None
    num_chunks: int
    status: str  # 'processing', 'ready', 'failed'
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Umożliwia konwersję z ORM models


class RAGUploadRequest(BaseModel):
    """
    Request schema dla uploadu dokumentu

    Używane jako Form data (nie JSON).
    """
    title: str = Field(..., min_length=1, max_length=255, description="Tytuł dokumentu")
    country: str = Field(
        default="Poland",
        max_length=100,
        description="Kraj którego dotyczy dokument"
    )


class RAGQueryRequest(BaseModel):
    """
    Request schema dla testowego query RAG

    Używane w developer tools do testowania retrieval.
    """
    query: str = Field(..., min_length=1, description="Zapytanie tekstowe")
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Liczba wyników do zwrócenia (1-20)"
    )


class RAGQueryResponse(BaseModel):
    """
    Response schema dla query RAG

    Zawiera znalezione fragmenty i skonstruowany kontekst.
    """
    query: str
    results: List[Dict[str, Any]]  # Lista chunków z scores i metadata
    context: str  # Sklejony tekst z top wyników
    num_results: int


class RAGCitation(BaseModel):
    """
    Schema dla cytowania źródła RAG

    Przechowywane w JSONB w modelu Persona jako rag_citations.
    """
    text: str = Field(..., description="Fragment tekstu źródłowego")
    score: float = Field(..., description="Score similarity (0-1)")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata chunku (doc_id, title, etc.)"
    )


class PersonaGenerateRequestWithRAG(BaseModel):
    """
    Rozszerzony request do generowania person z opcją RAG

    Dodaje parametr use_rag do istniejącego PersonaGenerateRequest.
    """
    num_personas: int = Field(..., ge=1, le=100, description="Liczba person do wygenerowania")
    use_rag: bool = Field(
        default=True,
        description="Czy użyć RAG dla polskiej bazy wiedzy"
    )
    adversarial_mode: bool = Field(
        default=False,
        description="Tryb adversarial (większa różnorodność)"
    )
