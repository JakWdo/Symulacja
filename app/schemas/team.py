"""
Schematy Pydantic dla zespołów (teams)

Definiuje struktury danych dla operacji CRUD na teamach:
- TeamCreate - tworzenie nowego zespołu
- TeamUpdate - aktualizacja istniejącego zespołu
- TeamResponse - odpowiedź API z danymi zespołu
- TeamMembershipCreate - dodawanie członka do zespołu
- TeamMembershipResponse - odpowiedź z informacją o członkostwie
"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

from app.models.team import TeamRole


class TeamCreate(BaseModel):
    """
    Schema do tworzenia nowego zespołu

    Pola wymagane:
    - name: Nazwa zespołu (1-255 znaków)

    Pola opcjonalne:
    - description: Opis zespołu
    """
    name: str = Field(..., min_length=1, max_length=255, description="Nazwa zespołu")
    description: str | None = Field(None, description="Opcjonalny opis zespołu")


class TeamUpdate(BaseModel):
    """
    Schema do aktualizacji istniejącego zespołu

    Wszystkie pola opcjonalne - aktualizuj tylko to, co chcesz zmienić:
    - name: Nowa nazwa zespołu (1-255 znaków)
    - description: Nowy opis zespołu
    - is_active: Aktywny/nieaktywny (soft delete)

    Pola nie podane w requeście pozostają bez zmian.
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class TeamMemberInfo(BaseModel):
    """
    Informacje o członku zespołu (użytkownik + rola)
    """
    user_id: UUID
    email: str
    full_name: str
    role_in_team: TeamRole
    joined_at: datetime

    model_config = {"from_attributes": True}


class TeamResponse(BaseModel):
    """
    Schema odpowiedzi API z danymi zespołu

    Zwraca kompletne informacje o zespole włącznie z:

    Podstawowe dane:
    - id: UUID zespołu
    - name: Nazwa zespołu
    - description: Opis zespołu
    - is_active: Czy zespół jest aktywny

    Metadata:
    - created_at: Data utworzenia zespołu
    - updated_at: Data ostatniej aktualizacji
    - member_count: Liczba członków zespołu (opcjonalne)
    - project_count: Liczba projektów w zespole (opcjonalne)

    Konfiguracja:
    - from_attributes = True: Umożliwia tworzenie z modeli SQLAlchemy
    """
    id: UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Opcjonalne liczniki (wypełniane tylko gdy zapytano o szczegóły)
    member_count: int | None = None
    project_count: int | None = None
    members: list[TeamMemberInfo] | None = None

    model_config = {"from_attributes": True}


class TeamMembershipCreate(BaseModel):
    """
    Schema do dodawania członka do zespołu

    Pola wymagane:
    - user_id: UUID użytkownika do dodania (lub email)
    - role_in_team: Rola w zespole (owner|member|viewer)

    Uwaga: Użytkownik może być w teamie tylko raz (constraint UNIQUE)
    """
    user_id: UUID | None = None
    email: str | None = None  # Alternatywnie można podać email zamiast user_id
    role_in_team: TeamRole = Field(default=TeamRole.MEMBER)


class TeamMembershipUpdate(BaseModel):
    """
    Schema do aktualizacji roli członka zespołu

    Pola:
    - role_in_team: Nowa rola w zespole (owner|member|viewer)
    """
    role_in_team: TeamRole


class TeamMembershipResponse(BaseModel):
    """
    Schema odpowiedzi z informacją o członkostwie w zespole

    Zwraca:
    - id: UUID membership
    - team_id: UUID zespołu
    - user_id: UUID użytkownika
    - role_in_team: Rola użytkownika w zespole
    - created_at: Data dołączenia do zespołu

    Opcjonalnie (gdy zapytano o szczegóły):
    - team: Dane zespołu (TeamResponse)
    - user: Dane użytkownika (email, full_name)
    """
    id: UUID
    team_id: UUID
    user_id: UUID
    role_in_team: TeamRole
    created_at: datetime

    # Opcjonalne zagnieżdżone dane
    team: TeamResponse | None = None
    user_email: str | None = None
    user_full_name: str | None = None

    model_config = {"from_attributes": True}


class TeamListResponse(BaseModel):
    """
    Schema odpowiedzi z listą zespołów użytkownika

    Używane przez GET /teams/my - zwraca zespoły z rolami użytkownika
    """
    teams: list[TeamResponse]
    total: int
