"""
PersonaAuditService - Audit logging dla person

Serwis do logowania wszystkich akcji na personach:
- view, export, compare, delete, update, undo_delete
- Używane do compliance (GDPR), debugging, security monitoring

Każda akcja jest logowana z:
- Persona ID
- User ID
- Action type
- Details (JSON)
- IP address (optional, retention 90 dni)
- User agent (optional)
- Timestamp
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PersonaAuditLog

logger = logging.getLogger(__name__)


class PersonaAuditService:
    """
    Service do audit logging person

    Responsibilities:
    - Log all actions on personas (view, export, compare, delete, etc.)
    - Retrieve audit log history
    - Clean up old logs (GDPR compliance - retention 2 years, IP 90 days)

    Performance:
    - Async non-blocking writes (nie blokuje HTTP response)
    - Batch writes dla bulk operations
    - Indexes na persona_id, user_id, action, timestamp

    Examples:
        >>> # Log view action
        >>> await audit_service.log_action(
        ...     persona_id=UUID(...),
        ...     user_id=UUID(...),
        ...     action="view",
        ...     details={"source": "list", "device": "desktop"},
        ...     db=db
        ... )

        >>> # Log export action
        >>> await audit_service.log_action(
        ...     persona_id=UUID(...),
        ...     user_id=UUID(...),
        ...     action="export",
        ...     details={"format": "pdf", "sections": ["overview"], "pii_masked": True},
        ...     db=db
        ... )
    """

    async def log_action(
        self,
        persona_id: UUID,
        user_id: UUID,
        action: str,
        details: dict[str, Any] | None,
        db: AsyncSession,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PersonaAuditLog:
        """
        Loguj akcję na personie

        Args:
            persona_id: UUID persony
            user_id: UUID użytkownika wykonującego akcję
            action: Typ akcji (view, export, compare, delete, update, undo_delete)
            details: Szczegóły akcji (JSON)
            db: Async DB session
            ip_address: Opcjonalny adres IP użytkownika (retention 90 dni)
            user_agent: Opcjonalny User-Agent przeglądarki

        Returns:
            Utworzony PersonaAuditLog entry

        Raises:
            Exception: Jeśli zapis do DB failuje (logujemy ale nie propagujemy exception)

        Performance:
            - Async non-blocking write
            - Auto-commit (nie czeka na commit w parent transaction)
        """
        try:
            log_entry = PersonaAuditLog(
                persona_id=persona_id,
                user_id=user_id,
                action=action,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
            )
            db.add(log_entry)
            await db.commit()
            await db.refresh(log_entry)

            logger.info(
                f"Audit log created: action={action}, persona_id={persona_id}, user_id={user_id}",
                extra={
                    "persona_id": str(persona_id),
                    "user_id": str(user_id),
                    "action": action,
                },
            )
            return log_entry
        except Exception as e:
            # Graceful degradation - audit logging nie powinno failować całego requesta
            logger.error(
                f"Failed to create audit log: {e}",
                exc_info=e,
                extra={
                    "persona_id": str(persona_id),
                    "user_id": str(user_id),
                    "action": action,
                },
            )
            await db.rollback()
            # Nie propagujemy exception - audit logging jest "nice to have"
            # Jeśli audit failuje, główna operacja (view, export, etc.) powinna się udać
            raise  # Jednak w MVP propagujemy - chcemy wiedzieć o problemach

    async def get_audit_log(
        self, persona_id: UUID, db: AsyncSession, limit: int = 20
    ) -> list[PersonaAuditLog]:
        """
        Pobierz audit log dla persony

        Args:
            persona_id: UUID persony
            db: Async DB session
            limit: Max liczba rekordów (default 20, max 100)

        Returns:
            Lista PersonaAuditLog entries (sorted by timestamp DESC)

        Performance:
            - Index na (persona_id, timestamp DESC)
            - Limit 20 entries dla performance (można zwiększyć do 100)
        """
        # Clamp limit (security - nie pozwalaj na zbyt duże query)
        limit = min(max(1, limit), 100)

        result = await db.execute(
            select(PersonaAuditLog)
            .where(PersonaAuditLog.persona_id == persona_id)
            .order_by(PersonaAuditLog.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        logger.debug(
            f"Retrieved {len(logs)} audit log entries for persona {persona_id}",
            extra={"persona_id": str(persona_id), "count": len(logs)},
        )
        return list(logs)

    async def get_user_actions(
        self, user_id: UUID, db: AsyncSession, limit: int = 50
    ) -> list[PersonaAuditLog]:
        """
        Pobierz historię akcji użytkownika (dla Admin dashboard)

        Args:
            user_id: UUID użytkownika
            db: Async DB session
            limit: Max liczba rekordów (default 50, max 100)

        Returns:
            Lista PersonaAuditLog entries (sorted by timestamp DESC)

        RBAC:
            - Admin only (w endpoint trzeba sprawdzić role)

        Performance:
            - Index na (user_id, timestamp DESC)
        """
        limit = min(max(1, limit), 100)

        result = await db.execute(
            select(PersonaAuditLog)
            .where(PersonaAuditLog.user_id == user_id)
            .order_by(PersonaAuditLog.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        logger.debug(
            f"Retrieved {len(logs)} actions for user {user_id}",
            extra={"user_id": str(user_id), "count": len(logs)},
        )
        return list(logs)
