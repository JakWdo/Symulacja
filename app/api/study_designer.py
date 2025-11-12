"""
API endpoints dla Study Designer Chat

REST API dla interaktywnego projektowania badań przez chat.

Endpoints:
- POST   /study-designer/sessions - Rozpocznij nową sesję
- GET    /study-designer/sessions/{id} - Pobierz sesję
- POST   /study-designer/sessions/{id}/message - Wyślij wiadomość
- POST   /study-designer/sessions/{id}/approve - Zatwierdź plan
- DELETE /study-designer/sessions/{id} - Anuluj sesję
- GET    /study-designer/sessions - Lista sesji użytkownika
"""

from __future__ import annotations

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.study_designer import StudyDesignerSession
from app.services.study_designer.orchestrator import StudyDesignerOrchestrator
from app.schemas.study_designer import (
    SessionCreate,
    SessionCreateResponse,
    MessageSend,
    MessageSendResponse,
    PlanApproval,
    SessionResponse,
    SessionListResponse,
    MessageResponse,
    GeneratedPlanResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study-designer", tags=["study-designer"])


@router.post("/sessions", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rozpoczyna nową sesję projektowania badania.

    Returns:
        SessionCreateResponse z sesją i welcome message
    """
    logger.info(f"User {user.id} creating new study designer session")

    orchestrator = StudyDesignerOrchestrator(db)
    session = await orchestrator.create_session(
        user_id=user.id, project_id=data.project_id
    )

    # Get welcome message (last message from session)
    await db.refresh(session, attribute_names=["messages"])
    welcome_msg = session.messages[-1].content if session.messages else "Welcome!"

    return SessionCreateResponse(
        session=SessionResponse.from_orm(session), welcome_message=welcome_msg
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pobiera sesję z pełną historią wiadomości.

    Args:
        session_id: UUID sesji

    Returns:
        SessionResponse z messages
    """
    orchestrator = StudyDesignerOrchestrator(db)
    session = await orchestrator.get_session(session_id, user.id)

    # Convert generated_plan to response model
    response = SessionResponse.from_orm(session)

    if session.generated_plan:
        response.generated_plan = GeneratedPlanResponse(**session.generated_plan)

    return response


@router.post("/sessions/{session_id}/message", response_model=MessageSendResponse)
async def send_message(
    session_id: UUID,
    data: MessageSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Wysyła wiadomość do Study Designer.

    Args:
        session_id: UUID sesji
        data: MessageSend z treścią wiadomości

    Returns:
        MessageSendResponse z zaktualizowaną sesją i nowymi wiadomościami
    """
    logger.info(f"User {user.id} sending message to session {session_id}")

    orchestrator = StudyDesignerOrchestrator(db)

    # Verify user owns this session
    await orchestrator.get_session(session_id, user.id)

    # Count messages before (single query with eager loading)
    from sqlalchemy.orm import selectinload

    stmt = select(StudyDesignerSession).where(
        StudyDesignerSession.id == session_id
    ).options(selectinload(StudyDesignerSession.messages))

    result = await db.execute(stmt)
    session_before = result.scalar_one()

    messages_before_count = len(session_before.messages)

    # Process message
    session = await orchestrator.process_user_message(session_id, data.message)

    # Get new messages
    await db.refresh(session, attribute_names=["messages"])
    new_messages = session.messages[messages_before_count:]

    response = SessionResponse.from_orm(session)

    if session.generated_plan:
        response.generated_plan = GeneratedPlanResponse(**session.generated_plan)

    return MessageSendResponse(
        session=response,
        new_messages=[MessageResponse.from_orm(msg) for msg in new_messages],
        plan_ready=(session.status == "plan_ready"),
    )


@router.post("/sessions/{session_id}/message/stream")
async def send_message_stream(
    session_id: UUID,
    data: MessageSend,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE streaming endpoint dla Study Designer Chat.
    Zwraca partial messages w real-time podczas przetwarzania.

    Args:
        session_id: UUID sesji
        data: MessageSend z treścią wiadomości

    Returns:
        EventSourceResponse ze stream'em MessageChunk objects

    Events:
        - status: Initial status message
        - message: Partial assistant messages (MessageChunk)
        - error: Error details jeśli wystąpi błąd
    """
    logger.info(f"User {user.id} sending message (STREAM) to session {session_id}")

    orchestrator = StudyDesignerOrchestrator(db)

    # Verify user owns this session
    await orchestrator.get_session(session_id, user.id)

    async def event_generator():
        try:
            # Wrap całość w timeout (90s max - więcej niż state machine 60s)
            async with asyncio.timeout(90.0):
                # Initial status event
                yield {
                    "event": "status",
                    "data": json.dumps({"message": "Przetwarzanie pytania..."})
                }

                # Stream from orchestrator
                async for chunk in orchestrator.process_user_message_stream(
                    session_id, data.message
                ):
                    yield {
                        "event": "message",
                        "data": chunk.model_dump_json()
                    }

        except asyncio.TimeoutError:
            # API-level timeout
            logger.error(
                f"SSE stream timeout exceeded (90s) for session {session_id}",
                extra={
                    "session_id": str(session_id),
                    "user_id": str(user.id),
                    "timeout": 90.0
                }
            )
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": "timeout",
                    "message": "Request took too long (>90s). Please try again with a simpler query.",
                    "hint": "Break your question into smaller parts or be more specific"
                })
            }

        except HTTPException as e:
            # Forward HTTP errors (timeout from state machine, auth errors, etc.)
            logger.error(
                f"SSE stream HTTP error: {e.status_code} - {e.detail}",
                extra={"session_id": str(session_id), "status_code": e.status_code}
            )
            yield {
                "event": "error",
                "data": json.dumps({
                    "status_code": e.status_code,
                    "detail": e.detail
                })
            }

        except Exception as e:
            logger.error(
                f"SSE stream unexpected error: {e}",
                exc_info=True,
                extra={"session_id": str(session_id), "error_type": type(e).__name__}
            )
            yield {
                "event": "error",
                "data": json.dumps({
                    "error": "internal_error",
                    "detail": str(e)
                })
            }

    return EventSourceResponse(event_generator())


@router.post("/sessions/{session_id}/approve", response_model=SessionResponse)
async def approve_plan(
    session_id: UUID,
    data: PlanApproval,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Zatwierdza wygenerowany plan i uruchamia wykonanie badania.

    Args:
        session_id: UUID sesji
        data: PlanApproval (może być pusty)

    Returns:
        SessionResponse ze statusem approved/executing
    """
    logger.info(f"User {user.id} approving plan for session {session_id}")

    orchestrator = StudyDesignerOrchestrator(db)
    session = await orchestrator.approve_plan(session_id, user.id)

    response = SessionResponse.from_orm(session)

    if session.generated_plan:
        response.generated_plan = GeneratedPlanResponse(**session.generated_plan)

    return response


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_session(
    session_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Anuluje sesję projektowania badania.

    Args:
        session_id: UUID sesji
    """
    logger.info(f"User {user.id} cancelling session {session_id}")

    # Load session
    stmt = select(StudyDesignerSession).where(
        StudyDesignerSession.id == session_id,
        StudyDesignerSession.user_id == user.id,
    )
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    # Mark as cancelled
    session.status = "cancelled"
    session.completed_at = db.func.now()

    await db.commit()


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    """
    Lista sesji użytkownika (bez messages).

    Args:
        limit: Max liczba sesji (default 20)
        offset: Offset (default 0)

    Returns:
        SessionListResponse
    """
    logger.info(f"User {user.id} listing sessions (limit={limit}, offset={offset})")

    stmt = (
        select(StudyDesignerSession)
        .where(StudyDesignerSession.user_id == user.id)
        .order_by(StudyDesignerSession.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # Count total
    from sqlalchemy import func

    count_stmt = select(func.count(StudyDesignerSession.id)).where(
        StudyDesignerSession.user_id == user.id
    )
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    return SessionListResponse(
        sessions=[SessionResponse.from_orm(s) for s in sessions], total=total
    )
