"""Router FastAPI obsługujący operacje na bazie wiedzy RAG oraz Graph RAG."""

import logging
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.rag_document import RAGDocument
from app.models.user import User
from app.schemas.rag import (
    GraphRAGQuestionRequest,
    GraphRAGQuestionResponse,
    RAGCitation,
    RAGDocumentResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.services.rag import (
    RAGDocumentService,
    PolishSocietyRAG,
    GraphRAGService,
)

settings = get_settings()
router = APIRouter(prefix="/rag", tags=["RAG Knowledge Base"])
logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address)

_rag_document_service: RAGDocumentService | None = None
_polish_society_rag: PolishSocietyRAG | None = None
_graph_rag_service: GraphRAGService | None = None


def get_rag_document_service() -> RAGDocumentService:
    """Zwraca singleton serwisu dokumentów RAG."""

    global _rag_document_service
    if _rag_document_service is None:
        _rag_document_service = RAGDocumentService()
    return _rag_document_service


def get_polish_society_rag() -> PolishSocietyRAG:
    """Zwraca singleton odpowiedzialny za hybrydowe wyszukiwanie."""

    global _polish_society_rag
    if _polish_society_rag is None:
        _polish_society_rag = PolishSocietyRAG()
    return _polish_society_rag


def get_graph_rag_service() -> GraphRAGService:
    """Zwraca singleton serwisu Graph RAG."""

    global _graph_rag_service
    if _graph_rag_service is None:
        _graph_rag_service = GraphRAGService()
    return _graph_rag_service


async def _process_document_background(doc_id: uuid.UUID, file_path: str, metadata: dict) -> None:
    """Przetwarza dokument w tle i aktualizuje status w bazie danych."""

    async with AsyncSessionLocal() as db:
        try:
            logger.info("Rozpoczynam przetwarzanie dokumentu %s w tle", doc_id)
            service = get_rag_document_service()
            result = await service.ingest_document(file_path, metadata)

            doc = await db.get(RAGDocument, doc_id)
            if doc:
                doc.status = result["status"]
                doc.num_chunks = result.get("num_chunks", 0)
                doc.error_message = result.get("error")
                await db.commit()
                logger.info(
                    "Przetwarzanie dokumentu %s zakończone: status=%s, chunks=%s",
                    doc_id,
                    result["status"],
                    result.get("num_chunks"),
                )
        except Exception as exc:  # pragma: no cover - logujemy awarię background taska
            logger.error("Błąd podczas przetwarzania dokumentu %s: %s", doc_id, exc, exc_info=True)
            try:
                async with AsyncSessionLocal() as error_db:
                    doc = await error_db.get(RAGDocument, doc_id)
                    if doc:
                        doc.status = "failed"
                        doc.error_message = str(exc)
                        await error_db.commit()
            except Exception as update_exc:
                logger.error(
                    "Nie udało się zaktualizować statusu błędu dla dokumentu %s: %s",
                    doc_id,
                    update_exc,
                )


@router.post("/documents/upload", response_model=RAGDocumentResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("20/hour")  # Security: Limit document uploads (expensive processing)
async def upload_document(
    request: Request,  # Required by slowapi limiter
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    country: str = Form("Poland"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Przyjmuje dokument, zapisuje go na dysku i uruchamia asynchroniczne przetwarzanie."""

    # Security: Walidacja filename
    if not file.filename or '\0' in file.filename or len(file.filename) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nazwa pliku jest wymagana i musi być prawidłowa.",
        )

    # Security: Whitelist extension check
    extension = Path(file.filename).suffix.lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nieobsługiwany typ pliku: {extension}. Dozwolone: PDF, DOCX.",
        )

    # Security: File size limit (50MB default)
    max_size_bytes = settings.MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start

    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Plik za duży. Maksymalny rozmiar: {settings.MAX_DOCUMENT_SIZE_MB}MB (plik ma {file_size / 1024 / 1024:.1f}MB)",
        )

    storage_path = Path(settings.DOCUMENT_STORAGE_PATH)
    storage_path.mkdir(parents=True, exist_ok=True)

    # UUID w nazwie zapewnia unikalność i chroni przed path traversal
    stored_filename = f"{uuid.uuid4()}{extension}"
    stored_path = storage_path / stored_filename

    try:
        with stored_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info("Plik %s (%d bytes) zapisany jako %s", file.filename, file_size, stored_path)
    except Exception as exc:
        logger.error("Nie udało się zapisać pliku: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Nie udało się zapisać pliku na dysku.")

    document = RAGDocument(
        title=title,
        filename=file.filename,
        file_path=str(stored_path),
        file_type=extension.lstrip("."),
        country=country,
        status="processing",
        num_chunks=0,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    background_tasks.add_task(
        _process_document_background,
        document.id,
        str(stored_path),
        {"doc_id": str(document.id), "title": title, "country": country},
    )

    return document


@router.get("/documents", response_model=List[RAGDocumentResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Zwraca listę aktywnych dokumentów dostępnych w bazie wiedzy."""

    service = get_rag_document_service()
    documents = await service.list_documents(db)
    logger.info("Użytkownik %s pobrał listę %s dokumentów RAG", current_user.id, len(documents))
    return documents


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Wykonuje klasyczne zapytanie RAG (wyszukiwanie semantyczne lub hybrydowe)."""

    rag = get_polish_society_rag()
    if not rag.vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store nie jest dostępny.",
        )

    try:
        results = await rag.vector_store.asimilarity_search_with_score(request.query, k=request.top_k)
        context_chunks: List[str] = []
        citations: List[RAGCitation] = []
        for doc, score in results:
            context_chunks.append(doc.page_content)
            citations.append(
                RAGCitation(
                    document_title=doc.metadata.get("title", "Nieznany dokument"),
                    chunk_text=doc.page_content,
                    relevance_score=float(score),
                )
            )

        context = "\n\n---\n\n".join(context_chunks)
        return RAGQueryResponse(
            query=request.query,
            context=context,
            citations=citations,
            num_results=len(results),
        )
    except Exception as exc:
        logger.error("Błąd podczas zapytania RAG: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Zapytanie RAG nie powiodło się.")


@router.post("/query/graph", response_model=GraphRAGQuestionResponse)
async def query_graph_rag(
    request: GraphRAGQuestionRequest,
    current_user: User = Depends(get_current_user),
):
    """Zadaje pytanie do grafu wiedzy i zwraca wynik Graph RAG."""

    service = get_graph_rag_service()
    try:
        result = await service.answer_question(request.question)
        return GraphRAGQuestionResponse(**result)
    except Exception as exc:
        logger.error("Błąd podczas zapytania Graph RAG: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Nie udało się uzyskać odpowiedzi Graph RAG.")


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Usuwa dokument z bazy wiedzy oraz czyści powiązane dane w Neo4j."""

    service = get_rag_document_service()
    try:
        await service.delete_document(doc_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error("Błąd podczas usuwania dokumentu %s: %s", doc_id, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Nie udało się usunąć dokumentu.")

    return None