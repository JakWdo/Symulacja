"""
API endpoints dla Product Assistant Chat

Product Assistant to lightweight AI helper do pomocy użytkownikom w nawigacji
po platformie Sight. Stateless - NIE ZAPISUJE historii w DB.

Endpoints:
- POST /assistant/chat - Wysyła wiadomość do asystenta
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.assistant.assistant_service import AssistantService
from app.schemas.assistant import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Wysyła wiadomość do Product Assistant.

    Product Assistant odpowiada na pytania o funkcje platformy Sight,
    pomaga w nawigacji i wspiera użytkowników. NIE WYKONUJE żadnych akcji.

    Args:
        request: ChatRequest z wiadomością użytkownika, historią konwersacji
                 i flagą include_user_context
        user: Zalogowany użytkownik (dependency)
        db: Sesja bazodanowa (dependency)

    Returns:
        ChatResponse z odpowiedzią asystenta i sugestiami follow-up pytań

    Raises:
        HTTPException 500: Gdy wywołanie LLM failuje
    """
    logger.info(
        f"Product Assistant chat request from user {user.id}",
        extra={"user_id": str(user.id), "message_preview": request.message[:50]}
    )

    try:
        # Utwórz serwis i wywołaj chat
        service = AssistantService(db)
        response = await service.chat(
            user_id=user.id,
            message=request.message,
            conversation_history=request.conversation_history,
            include_user_context=request.include_user_context,
        )

        logger.info(
            f"Product Assistant responded to user {user.id}",
            extra={
                "user_id": str(user.id),
                "response_length": len(response["message"]),
                "suggestions_count": len(response["suggestions"])
            }
        )

        return ChatResponse(**response)

    except Exception as exc:
        logger.error(
            f"Product Assistant chat failed for user {user.id}: {exc}",
            exc_info=True,
            extra={"user_id": str(user.id)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Product Assistant jest tymczasowo niedostępny. Spróbuj ponownie za chwilę."
        )
