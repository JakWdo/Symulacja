"""
Model ORM dla Shared Context - środowiska, tagi, filtry, snapshoty

Tabele wspierające współdzielenie zasobów (persony, workflows) między projektami
na poziomie zespołu, z możliwością filtrowania przez tagi i tworzenia snapshotów.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text

from app.db.base import Base


class Environment(Base):
    """
    Model środowiska - workspace dla zasobów współdzielonych w teamie

    Reprezentuje logiczny kontener dla wspólnego poola zasobów (persony, workflows),
    który może być współdzielony między wieloma projektami w ramach teamu.

    Attributes:
        id: UUID środowiska (klucz główny)
        team_id: FK do teams - środowisko należy do konkretnego teamu
        name: Nazwa środowiska (np. "Production", "Testing", "Q1 Research Pool")
        description: Opcjonalny opis środowiska
        is_active: Czy środowisko jest aktywne (soft delete)
        created_at: Data utworzenia
        updated_at: Data ostatniej aktualizacji

    Relations:
        team: Team do którego należy środowisko
        projects: Lista projektów używających tego środowiska
        personas: Lista person w tym środowisku
        workflows: Lista workflow templates w tym środowisku
        resource_tags: Lista tagów zasobów w tym środowisku
        saved_filters: Lista zapisanych filtrów DSL
    """
    __tablename__ = "environments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relacje
    team = relationship("Team", back_populates="environments")
    projects = relationship(
        "Project",
        back_populates="environment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    personas = relationship(
        "Persona",
        back_populates="environment"
    )
    workflows = relationship(
        "Workflow",
        back_populates="environment"
    )
    resource_tags = relationship(
        "ResourceTag",
        back_populates="environment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    saved_filters = relationship(
        "SavedFilter",
        back_populates="environment",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Environment id={self.id} name={self.name!r} team_id={self.team_id}>"


class Tag(Base):
    """
    Model tagu - semantyczne oznaczenia zasobów z facetami

    Reprezentuje pojedynczy tag z systemem facet:key (np. "dem:age-25-34", "geo:warsaw").
    Tagi są współdzielone globalnie i używane do filtrowania zasobów w środowiskach.

    Attributes:
        id: UUID tagu (klucz główny)
        facet: Kategoria tagu (dem, geo, psy, biz, ctx, custom)
        key: Klucz tagu w formacie kebab-case lub snake_case
        description: Opcjonalny opis tagu
        created_at: Data utworzenia

    Relations:
        resource_tags: Lista powiązań zasobów z tym tagiem

    Constraints:
        - Unikalność (facet, key): kombinacja facet:key musi być unikalna

    Przykłady:
        - dem:age-25-34 (demografia: wiek 25-34)
        - geo:warsaw (geografia: Warszawa)
        - psy:high-openness (psychologia: wysoka otwartość)
        - biz:premium-segment (biznes: segment premium)
        - ctx:holiday-shopping (kontekst: zakupy świąteczne)
    """
    __tablename__ = "tags"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facet = Column(String(50), nullable=False, index=True)  # dem, geo, psy, biz, ctx, custom
    key = Column(String(100), nullable=False, index=True)   # age-25-34, warsaw, etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    resource_tags = relationship(
        "ResourceTag",
        back_populates="tag",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Tag id={self.id} facet={self.facet!r} key={self.key!r}>"


class ResourceTag(Base):
    """
    Model powiązania zasobu z tagiem - many-to-many dla tagowania

    Reprezentuje przypisanie tagu do konkretnego zasobu (persona, workflow, etc.)
    w ramach środowiska. Umożliwia filtrowanie zasobów przez tagi.

    Attributes:
        id: UUID powiązania (klucz główny)
        environment_id: FK do environments - w jakim środowisku jest tagowany zasób
        resource_type: Typ zasobu (persona, workflow, focus_group, etc.)
        resource_id: UUID zasobu
        tag_id: FK do tags - który tag jest przypisany
        created_at: Data przypisania tagu

    Relations:
        environment: Środowisko w którym jest zasób
        tag: Tag przypisany do zasobu

    Constraints:
        - Unikalność (environment_id, resource_type, resource_id, tag_id):
          ten sam tag nie może być przypisany dwa razy do tego samego zasobu
        - Index na (environment_id, resource_type) dla szybkiego filtrowania
        - Index na (tag_id) dla zapytań "które zasoby mają ten tag"
    """
    __tablename__ = "resource_tags"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    environment_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    resource_type = Column(String(50), nullable=False, index=True)  # persona, workflow, etc.
    resource_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    tag_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    environment = relationship("Environment", back_populates="resource_tags")
    tag = relationship("Tag", back_populates="resource_tags")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ResourceTag resource_type={self.resource_type!r} resource_id={self.resource_id} tag_id={self.tag_id}>"


class SavedFilter(Base):
    """
    Model zapisanego filtra - wielokrotnie używalne zapytania DSL

    Reprezentuje zapisane zapytanie filtrujące w DSL (Domain Specific Language),
    które użytkownik może wielokrotnie wykorzystywać do filtrowania zasobów.

    Attributes:
        id: UUID filtra (klucz główny)
        environment_id: FK do environments - filtr jest zapisany w kontekście środowiska
        name: Nazwa filtra (np. "Young professionals in Warsaw", "High openness personas")
        dsl: Zapytanie DSL (np. "dem:age-25-34 AND geo:warsaw AND psy:high-openness")
        created_by: FK do users - kto utworzył filtr
        created_at: Data utworzenia

    Relations:
        environment: Środowisko w którym jest zapisany filtr
        creator: Użytkownik który utworzył filtr

    Przykłady DSL:
        - "dem:age-25-34 AND geo:warsaw"
        - "(psy:high-openness OR psy:high-extraversion) AND NOT dem:age-55-plus"
        - "biz:premium-segment AND ctx:holiday-shopping"
    """
    __tablename__ = "saved_filters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    environment_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    dsl = Column(Text, nullable=False)  # DSL query string
    created_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    environment = relationship("Environment", back_populates="saved_filters")
    creator = relationship("User")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SavedFilter id={self.id} name={self.name!r}>"


class ProjectSnapshot(Base):
    """
    Model snapshotu projektu - immutable zestaw zasobów dla reprodukowalności

    Reprezentuje "zamrożony" snapshot zasobów (persony, workflows, etc.) przypisanych
    do projektu w konkretnym momencie czasu. Zapewnia reprodukowalność badań nawet
    jeśli pool zasobów w środowisku się zmieni.

    Attributes:
        id: UUID snapshotu (klucz główny)
        project_id: FK do projects - snapshot należy do konkretnego projektu
        name: Nazwa snapshotu (np. "Initial research snapshot", "Final personas v2")
        resource_type: Typ zasobów w snapshot (persona, workflow, etc.)
        resource_ids: Lista UUID zasobów (JSONB array)
        created_at: Data utworzenia snapshotu

    Relations:
        project: Projekt do którego należy snapshot

    Uwagi:
        - Snapshot jest immutable - nie może być modyfikowany po utworzeniu
        - resource_ids to lista UUID w formacie JSONB: ["uuid1", "uuid2", ...]
        - Jeden projekt może mieć wiele snapshotów (np. różne wersje, różne typy zasobów)
    """
    __tablename__ = "project_snapshots"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)  # persona, workflow, etc.
    resource_ids = Column(JSONB, nullable=False)  # Array of UUIDs: ["uuid1", "uuid2", ...]
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacje
    project = relationship("Project", back_populates="snapshots")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ProjectSnapshot id={self.id} name={self.name!r} project_id={self.project_id}>"
