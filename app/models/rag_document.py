"""
Model ORM dla dokumentów RAG (Retrieval-Augmented Generation)

Tabela `rag_documents` przechowuje metadane przetworzonych dokumentów
używanych jako baza wiedzy dla systemu RAG.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func, text

from app.db.base import Base


class RAGDocument(Base):
    """
    Model dokumentu RAG - źródło wiedzy dla generowania person

    Reprezentuje pojedynczy dokument (PDF, DOCX) przetworzony przez system RAG.
    Dokument jest dzielony na chunki, które są następnie indeksowane w Neo4j
    z embeddingami dla semantic search.

    Attributes:
        # === IDENTYFIKATORY ===
        id: UUID dokumentu (klucz główny)

        # === METADANE PLIKU ===
        title: Tytuł dokumentu (nadany przez użytkownika)
        filename: Nazwa pliku oryginalnego
        file_path: Ścieżka do pliku w systemie plików
        file_type: Typ pliku ('pdf' lub 'docx')

        # === METADANE TREŚCI ===
        country: Kraj którego dotyczy dokument (domyślnie 'Poland')
        date: Rok publikacji (opcjonalny, float dla elastyczności)

        # === STATUS PRZETWARZANIA ===
        num_chunks: Liczba chunków tekstowych wygenerowanych z dokumentu
        status: Status przetwarzania ('processing', 'ready', 'failed')
        error_message: Komunikat błędu (jeśli status = 'failed')

        # === TIMESTAMPS ===
        created_at: Data dodania dokumentu do systemu
        updated_at: Data ostatniej aktualizacji
        is_active: Czy dokument jest aktywny (soft delete)

    Lifecycle:
        1. Upload pliku → status='processing', num_chunks=0
        2. Przetwarzanie (parsing, chunking, embedding) → background task
        3. Sukces → status='ready', num_chunks=X
        4. Błąd → status='failed', error_message='...'
        5. Usunięcie → is_active=False (chunks usuwane z Neo4j)
    """
    __tablename__ = "rag_documents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Metadane pliku
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False)  # 'pdf', 'docx'

    # Metadane treści
    country = Column(String(100), nullable=True, default='Poland')
    date = Column(Float, nullable=True)  # Rok publikacji jako float

    # Status przetwarzania
    num_chunks = Column(Integer, nullable=False, default=0, server_default=text("0"))
    status = Column(
        String(50),
        nullable=False,
        default='processing',
        server_default=text("'processing'")
    )
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))

    def __repr__(self) -> str:
        return f"<RAGDocument(id={self.id}, title='{self.title}', status='{self.status}', chunks={self.num_chunks})>"
