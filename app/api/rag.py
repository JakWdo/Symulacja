"""
API Endpoints dla RAG (Retrieval-Augmented Generation)

System bazy wiedzy do generowania person opartych na rzeczywistych danych.

Endpointy:
- POST /rag/documents/upload - Upload i przetwórz dokument PDF/DOCX
- GET /rag/documents - Lista przetworzonych dokumentów
- POST /rag/query - Test RAG retrieval (developer tool)
- DELETE /rag/documents/{doc_id} - Usuń dokument z bazy wiedzy
"""

import shutil
import logging
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db, AsyncSessionLocal
from app.models import User, RAGDocument
from app.api.dependencies import get_current_user
from app.schemas.rag import (
    RAGDocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGCitation,
)
from app.services.rag_service import RAGDocumentService, PolishSocietyRAG
from app.core.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])
logger = logging.getLogger(__name__)


# Singleton instances (cache)
_rag_document_service: RAGDocumentService | None = None
_polish_society_rag: PolishSocietyRAG | None = None


def get_rag_document_service() -> RAGDocumentService:
    """Pobierz singleton RAGDocumentService"""
    global _rag_document_service
    if _rag_document_service is None:
        _rag_document_service = RAGDocumentService()
    return _rag_document_service


def get_polish_society_rag() -> PolishSocietyRAG:
    """Pobierz singleton PolishSocietyRAG"""
    global _polish_society_rag
    if _polish_society_rag is None:
        _polish_society_rag = PolishSocietyRAG()
    return _polish_society_rag


async def _process_document_background(
    doc_id: UUID,
    file_path: str,
    metadata: dict,
):
    """
    Background task do przetwarzania dokumentu

    Wykonuje:
    1. Parsing dokumentu (PDF/DOCX)
    2. Chunking tekstu
    3. Generowanie embeddingów
    4. Zapis w Neo4j
    5. Update statusu w PostgreSQL

    Args:
        doc_id: UUID dokumentu w PostgreSQL
        file_path: Ścieżka do pliku
        metadata: Metadane dokumentu
    """
    async with AsyncSessionLocal() as db:
        try:
            logger.info(f"Starting background processing for document {doc_id}")

            # Ingest document
            service = get_rag_document_service()
            result = await service.ingest_document(file_path, metadata)

            # Update status w PostgreSQL
            doc = await db.get(RAGDocument, doc_id)
            if doc:
                doc.status = result['status']
                doc.num_chunks = result['num_chunks']
                if result.get('error'):
                    doc.error_message = result['error']
                await db.commit()

                logger.info(
                    f"Document {doc_id} processing completed: "
                    f"status={result['status']}, chunks={result['num_chunks']}"
                )

        except Exception as e:
            logger.error(f"Document {doc_id} processing failed: {e}", exc_info=True)

            # Update status na failed
            try:
                async with AsyncSessionLocal() as error_db:
                    doc = await error_db.get(RAGDocument, doc_id)
                    if doc:
                        doc.status = 'failed'
                        doc.error_message = str(e)
                        await error_db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update error status: {update_error}")


@router.post("/documents/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    country: str = Form("Poland"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload dokumentu PDF lub DOCX do bazy wiedzy

    Dokument jest przetwarzany w tle (background task).
    Endpoint zwraca 202 Accepted natychmiast.

    Proces:
    1. Walidacja typu pliku (PDF, DOCX)
    2. Zapis pliku na dysk
    3. Utworzenie rekordu w PostgreSQL (status='processing')
    4. Background task: parsing → chunking → embedding → Neo4j
    5. Update statusu na 'ready' lub 'failed'

    Args:
        file: Plik do uploadu (PDF lub DOCX)
        title: Tytuł dokumentu (nadany przez użytkownika)
        country: Kraj którego dotyczy dokument (default: Poland)
        current_user: Zalogowany użytkownik
        db: Sesja bazy danych

    Returns:
        Dict z id dokumentu i komunikatem o przetwarzaniu w tle

    Raises:
        HTTPException 400: Nieobsługiwany typ pliku
        HTTPException 500: Błąd zapisu pliku
    """
    # Walidacja typu pliku
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ['.pdf', '.docx']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_extension}. Supported: PDF, DOCX"
        )

    logger.info(f"Received upload request: {file.filename} (type: {file_extension})")

    # Utwórz folder jeśli nie istnieje
    storage_path = Path(settings.DOCUMENT_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    # Zapisz plik z unikalną nazwą (używamy UUID)
    import uuid
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = storage_path / unique_filename

    try:
        # Zapisz plik na dysk
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved to: {file_path}")

    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Utwórz rekord w PostgreSQL
    doc = RAGDocument(
        title=title,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_extension[1:],  # Bez kropki: 'pdf', 'docx'
        country=country,
        status='processing',
        num_chunks=0,
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    logger.info(f"Created RAGDocument record: {doc.id}")

    # Dodaj background task do przetworzenia dokumentu
    background_tasks.add_task(
        _process_document_background,
        doc.id,
        str(file_path),
        {
            'doc_id': str(doc.id),
            'title': title,
            'country': country,
        }
    )

    return {
        "id": doc.id,
        "message": "Dokument jest przetwarzany w tle. Sprawdź status za chwilę.",
        "status": "processing"
    }


@router.get("/documents", response_model=List[RAGDocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista wszystkich przetworzonych dokumentów RAG

    Zwraca tylko aktywne dokumenty (is_active=True).
    Posortowane od najnowszych.

    Returns:
        Lista dokumentów z metadanymi i statusami

    Response fields:
        - id: UUID dokumentu
        - title: Tytuł nadany przez użytkownika
        - filename: Oryginalna nazwa pliku
        - file_type: 'pdf' lub 'docx'
        - country: Kraj
        - num_chunks: Liczba chunków (0 jeśli processing/failed)
        - status: 'processing', 'ready', 'failed'
        - error_message: Komunikat błędu (jeśli failed)
        - created_at: Data uploadu
    """
    service = get_rag_document_service()
    documents = await service.list_documents(db)

    logger.info(f"Listed {len(documents)} RAG documents for user {current_user.id}")

    return documents


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Test RAG retrieval - developer tool

    Wykonuje semantic search w bazie wiedzy i zwraca top-K wyników.
    Używane do testowania jakości retrieval.

    Args:
        request: Query + top_k (liczba wyników)
        current_user: Zalogowany użytkownik

    Returns:
        Query response z wynikami i kontekstem

    Response fields:
        - query: Zapytanie użytkownika
        - results: Lista chunków (text, score, metadata)
        - context: Sklejony tekst z top wyników
        - num_results: Liczba znalezionych wyników
    """
    logger.info(f"RAG query request: '{request.query[:100]}...' (top_k={request.top_k})")

    rag = get_polish_society_rag()

    # Simple search (nie demographic-specific, tylko raw query)
    try:
        if not rag.vector_store:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG vector store is not available"
            )

        # Semantic search
        results = await rag.vector_store.asimilarity_search_with_score(
            request.query,
            k=request.top_k
        )

        # Build response
        context_chunks = []
        citations = []

        for doc, score in results:
            chunk_text = doc.page_content
            context_chunks.append(chunk_text)

            # Dodaj document_title z metadata
            metadata = doc.metadata.copy()
            doc_title = metadata.get("document_title", "Unknown Document")

            citations.append(RAGCitation(
                document_title=doc_title,
                chunk_text=chunk_text,
                relevance_score=float(score)
            ))

        context = "\n\n---\n\n".join(context_chunks)

        logger.info(f"RAG query returned {len(results)} results")

        return RAGQueryResponse(
            query=request.query,
            context=context,
            citations=citations,
            num_results=len(results)
        )

    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG query failed: {str(e)}"
        )


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Usuń dokument z bazy wiedzy

    Wykonuje:
    1. Soft delete w PostgreSQL (is_active=False)
    2. Usunięcie chunków z Neo4j

    Args:
        doc_id: UUID dokumentu do usunięcia
        current_user: Zalogowany użytkownik
        db: Sesja bazy danych

    Returns:
        HTTP 204 No Content (success)

    Raises:
        HTTPException 404: Dokument nie istnieje
    """
    logger.info(f"Delete request for document {doc_id} by user {current_user.id}")

    service = get_rag_document_service()

    try:
        await service.delete_document(doc_id, db)
        logger.info(f"Document {doc_id} deleted successfully")
        return None

    except ValueError as e:
        logger.warning(f"Document not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to delete document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
