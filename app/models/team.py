"""
Model ORM dla zespołów (teams)

Tabela `teams` reprezentuje przestrzenie współpracy zespołowej w systemie Sight.
Każdy team może mieć wiele użytkowników (przez team_memberships) i wiele projektów.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text, Enum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base


class TeamRole(str, enum.Enum):
    """
    Role użytkownika w zespole (team-level permissions).

    Roles:
    - OWNER: Pełne uprawnienia do zarządzania teamem (dodawanie/usuwanie członków, usunięcie teamu)
    - MEMBER: Może tworzyć i edytować projekty w teamie
    - VIEWER: Tylko odczyt projektów w teamie (nie może tworzyć/edytować)

    Uwaga: TeamRole to uprawnienia w teamie, SystemRole to globalne uprawnienia w systemie.
    Efektywne uprawnienia = min(SystemRole, TeamRole)
    """
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"


class Team(Base):
    """
    Model zespołu (team workspace)

    Reprezentuje przestrzeń współpracy zespołowej, która:
    - Grupuje projektów badawczych
    - Zarządza członkami zespołu z rolami
    - Izoluje dane między teamami

    Attributes:
        id: UUID teamu (klucz główny)
        name: Nazwa teamu (np. "Marketing Team", "Product Research")
        description: Opcjonalny opis teamu
        is_active: Czy team jest aktywny (soft delete)
        created_at: Data utworzenia
        updated_at: Data ostatniej aktualizacji

    Relations:
        memberships: Lista członków teamu (przez TeamMembership)
        projects: Lista projektów należących do teamu
    """
    __tablename__ = "teams"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relacje
    memberships = relationship(
        "TeamMembership",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    projects = relationship(
        "Project",
        back_populates="team",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Team id={self.id} name={self.name!r}>"


class TeamMembership(Base):
    """
    Model przynależności użytkownika do zespołu

    Reprezentuje relację many-to-many między User i Team z dodatkową rolą.
    Każdy użytkownik może być członkiem wielu teamów, a każdy team może mieć wielu użytkowników.

    Attributes:
        id: UUID membership (klucz główny)
        team_id: FK do teams
        user_id: FK do users
        role_in_team: Rola użytkownika w teamie (owner|member|viewer)
        created_at: Data dołączenia do teamu

    Relations:
        team: Team do którego należy użytkownik
        user: Użytkownik będący członkiem teamu

    Constraints:
        - Unikalność (team_id, user_id): użytkownik może być w teamie tylko raz
    """
    __tablename__ = "team_memberships"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    role_in_team = Column(
        Enum(TeamRole, name='team_role_enum', create_type=False, values_callable=lambda x: [m.value for m in x]),
        nullable=False,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    team = relationship("Team", back_populates="memberships")
    user = relationship("User", back_populates="team_memberships")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<TeamMembership team_id={self.team_id} user_id={self.user_id} role={self.role_in_team.value}>"
