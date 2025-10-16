"""
Model ORM dla audit log person

Tabela `persona_audit_log` przechowuje pełną historię akcji na personach:
- view, export, compare, delete, update, undo_delete
- Używane do compliance (GDPR), debugging, security monitoring
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models import Persona, User


class PersonaAuditLog(Base):
    """
    Audit log dla wszystkich akcji na personach

    Każda akcja użytkownika (view, export, compare, delete, update) jest logowana.
    Używane do compliance (GDPR), debugging, security monitoring.

    Attributes:
        id: UUID logu (klucz główny)
        persona_id: UUID persony której dotyczy akcja
        user_id: UUID użytkownika wykonującego akcję (nullable - może być NULL jeśli user usunięty)
        action: Typ akcji (view, export, compare, delete, update, undo_delete)
        details: Szczegóły akcji w formacie JSON (np. export format, sections exported)
        ip_address: Adres IP użytkownika (IPv4/IPv6) - retention 90 dni zgodnie z GDPR
        user_agent: User-Agent przeglądarki (do analizy urządzeń)
        timestamp: Data i czas akcji (z timezone)

    Relations:
        persona: Persona której dotyczy log
        user: Użytkownik wykonujący akcję

    Examples:
        >>> # View action
        >>> log = PersonaAuditLog(
        ...     persona_id=persona.id,
        ...     user_id=user.id,
        ...     action="view",
        ...     details={"source": "list", "device": "desktop"},
        ...     ip_address="192.168.1.1",
        ...     user_agent="Mozilla/5.0..."
        ... )

        >>> # Export action
        >>> log = PersonaAuditLog(
        ...     persona_id=persona.id,
        ...     user_id=user.id,
        ...     action="export",
        ...     details={
        ...         "format": "pdf",
        ...         "sections": ["overview", "profile", "behaviors"],
        ...         "pii_masked": True,
        ...         "file_size_kb": 850
        ...     }
        ... )
    """

    __tablename__ = "persona_audit_log"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    persona_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(
        String(100), nullable=False, index=True
    )  # view, export, compare, delete, update, undo_delete
    details = Column(
        JSON, nullable=True
    )  # Szczegóły akcji (np. export format, sections exported)
    ip_address = Column(
        String(45), nullable=True
    )  # IPv4/IPv6 (GDPR: retention 90 days)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    # Relacje
    persona = relationship("Persona", back_populates="audit_logs")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PersonaAuditLog action={self.action} persona_id={self.persona_id}>"
