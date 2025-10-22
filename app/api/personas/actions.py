"""
API Endpoints - Persona Actions

Akcje na personach:
- POST /personas/{persona_id}/actions/compare - porównaj persony (PersonaComparisonService)
- [ARCHIVED] POST /personas/{persona_id}/actions/messaging - wygeneruj messaging (PersonaMessagingService)

UWAGA: Messaging endpoint jest zarchiwizowany (PersonaMessagingService moved to app/services/archived/)
Feature nie jest używany w frontend UI. Można przywrócić gdy będzie implementacja UI.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import User
from app.services.personas import PersonaAuditService, PersonaComparisonService
from app.api.dependencies import get_current_user, get_persona_for_user
from app.schemas.persona_details import (
    PersonaComparisonRequest,
    PersonaComparisonResponse,
    # PersonaMessagingRequest,
    # PersonaMessagingResponse,
)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


@router.post(
    "/personas/{persona_id}/actions/compare",
    response_model=PersonaComparisonResponse,
)
@limiter.limit("30/minute")
async def compare_personas_endpoint(
    request: Request,  # Required by slowapi limiter
    persona_id: UUID,
    payload: PersonaComparisonRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    primary_persona = await get_persona_for_user(persona_id, current_user, db)
    comparison_service = PersonaComparisonService(db)
    data = await comparison_service.compare_personas(
        primary_persona,
        [str(pid) for pid in payload.persona_ids],
        sections=payload.sections,
    )

    audit_service = PersonaAuditService()
    await audit_service.log_action(
        persona_id=persona_id,
        user_id=current_user.id,
        action="compare",
        details={
            "persona_ids": [str(pid) for pid in payload.persona_ids],
            "sections": payload.sections,
        },
        db=db,
    )

    return PersonaComparisonResponse(**data)


# ARCHIVED ENDPOINT - PersonaMessagingService moved to app/services/archived/
# Feature nie jest używane w frontend UI
# Można przywrócić gdy będzie implementacja UI lub decyzja o rozwoju feature
#
# @router.post(
#     "/personas/{persona_id}/actions/messaging",
#     response_model=PersonaMessagingResponse,
# )
# @limiter.limit("10/hour")
# async def generate_persona_messaging(
#     request: Request,  # Required by slowapi limiter
#     persona_id: UUID,
#     payload: PersonaMessagingRequest,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     from app.services.archived.messaging import PersonaMessagingService
#     persona = await get_persona_for_user(persona_id, current_user, db)
#     messaging_service = PersonaMessagingService()
#     result = await messaging_service.generate_messaging(
#         persona,
#         tone=payload.tone,
#         message_type=payload.message_type,
#         num_variants=payload.num_variants,
#         context=payload.context,
#     )
#
#     audit_service = PersonaAuditService()
#     await audit_service.log_action(
#         persona_id=persona_id,
#         user_id=current_user.id,
#         action="messaging",
#         details={
#             "tone": payload.tone,
#             "type": payload.message_type,
#             "variants": payload.num_variants,
#         },
#         db=db,
#     )
#
#     return PersonaMessagingResponse(**result)
