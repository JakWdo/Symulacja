"""
Persona Details CRUD - Operacje bazodanowe dla szczegółowego widoku persony

Funkcje pomocnicze do:
- Pobierania audit log
- Logowania view events
- Persystowania pól JSONB
"""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import AsyncSessionLocal
from app.models import Persona
from app.services.personas.persona_audit_service import PersonaAuditService
from app.schemas.persona_details import PersonaAuditEntry
from app.core.redis import redis_delete

logger = logging.getLogger(__name__)


async def fetch_audit_log(
    persona_id: UUID,
    db: AsyncSession,
    audit_service: PersonaAuditService,
) -> list[PersonaAuditEntry]:
    """
    Fetch audit log (last 20 actions)

    Args:
        persona_id: UUID persony
        db: AsyncSession
        audit_service: PersonaAuditService instance

    Returns:
        Lista PersonaAuditEntry (last 20 actions)

    Performance:
        - Index na (persona_id, timestamp DESC)
        - Limit 20 entries
    """
    try:
        logs = await audit_service.get_audit_log(persona_id, db, limit=20)
        return [
            PersonaAuditEntry(
                id=log.id,
                action=log.action,
                details=log.details,
                user_id=log.user_id,
                timestamp=log.timestamp,
            )
            for log in logs
        ]
    except Exception as e:
        logger.error(
            f"Failed to fetch audit log for persona {persona_id}: {e}", exc_info=e
        )
        return []


async def log_view_event(persona_id: UUID, user_id: UUID):
    """
    Log view event (async, non-blocking)

    Args:
        persona_id: UUID persony
        user_id: UUID użytkownika

    Note:
        To jest async task (create_task) - nie blokuje HTTP response
        Jeśli failuje, logujemy warning ale nie propagujemy exception
    """
    try:
        async with AsyncSessionLocal() as audit_db:
            audit_service = PersonaAuditService()
            await audit_service.log_action(
                persona_id=persona_id,
                user_id=user_id,
                action="view",
                details={"source": "detail_view", "device": "web"},
                db=audit_db,
            )
    except Exception as e:
        logger.warning("Failed to log view event: %s", e)


async def persist_persona_field(persona_id: UUID, field_name: str, value: dict) -> None:
    """
    Persist a JSONB field on Persona in a dedicated transaction.

    Args:
        persona_id: UUID persony
        field_name: Nazwa pola do aktualizacji (np. "needs_and_pains")
        value: Wartość do zapisania (dict)

    Note:
        - Używa dedykowanej sesji do persystencji
        - Invaliduje cache po zapisie
        - Jeśli failuje, loguje warning ale nie propaguje exception
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Persona).where(Persona.id == persona_id))
            persona = result.scalars().first()
            if not persona:
                logger.warning("Persona %s not found when persisting %s", persona_id, field_name)
                return

            setattr(persona, field_name, value)
            await session.commit()
            logger.debug("Persisted %s for persona %s", field_name, persona_id)
            await redis_delete(f"persona_details:{persona_id}")
    except Exception as exc:
        logger.warning("Failed to persist %s for persona %s: %s", field_name, persona_id, exc)
