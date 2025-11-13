"""
API Endpoints dla Zarządzania Zespołami (Teams)

Ten moduł zawiera endpointy dla zarządzania zespołami i członkami zespołów:
- POST /teams - Tworzenie nowego zespołu
- GET /teams/my - Lista zespołów użytkownika
- GET /teams/{id} - Szczegóły zespołu
- PUT /teams/{id} - Aktualizacja zespołu
- DELETE /teams/{id} - Usunięcie zespołu (soft delete)
- POST /teams/{id}/members - Dodawanie członka do zespołu
- DELETE /teams/{id}/members/{user_id} - Usuwanie członka z zespołu
- PUT /teams/{id}/members/{user_id} - Aktualizacja roli członka

Zespoły umożliwiają współpracę i dzielenie projektów między użytkownikami.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID

from app.db import get_db
from app.models import Team, TeamMembership, User, Project
from app.models.team import TeamRole
from app.api.dependencies import (
    get_current_user,
    get_current_researcher_user,
    get_team_for_user,
    require_team_membership,
)
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamMembershipCreate,
    TeamMembershipUpdate,
    TeamMembershipResponse,
    TeamListResponse,
    TeamMemberInfo,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/teams", response_model=TeamResponse, status_code=201, tags=["Teams"])
async def create_team(
    team: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_researcher_user),
):
    """
    Utwórz nowy zespół

    Tworzenie zespołu jest dostępne dla użytkowników z rolą RESEARCHER lub wyższą.
    Użytkownik tworzący zespół automatycznie zostaje jego właścicielem (OWNER).

    Args:
        team: Dane nowego zespołu (name, description)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Utworzony zespół z ID i timestampami

    Raises:
        HTTPException 403: Jeśli użytkownik ma tylko rolę VIEWER
        HTTPException 422: Jeśli dane są niepoprawne (walidacja Pydantic)
    """
    # Utwórz zespół
    db_team = Team(
        name=team.name,
        description=team.description,
        is_active=True,
    )

    db.add(db_team)
    await db.flush()  # Flush aby mieć ID zespołu

    # Dodaj użytkownika jako właściciela zespołu
    db_membership = TeamMembership(
        team_id=db_team.id,
        user_id=current_user.id,
        role_in_team=TeamRole.OWNER,
    )

    db.add(db_membership)
    await db.commit()
    await db.refresh(db_team)

    logger.info(
        "Team created",
        extra={
            "team_id": str(db_team.id),
            "team_name": db_team.name,
            "owner_id": str(current_user.id),
        }
    )

    return db_team


@router.get("/teams/my", response_model=TeamListResponse, tags=["Teams"])
async def list_my_teams(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz listę zespołów użytkownika

    Zwraca wszystkie zespoły, w których użytkownik jest członkiem.
    Admin widzi wszystkie zespoły w systemie.

    Args:
        skip: Offset dla paginacji (domyślnie 0)
        limit: Limit wyników (domyślnie 100, max 100)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Lista zespołów z podstawowymi informacjami
    """
    from app.models.user import SystemRole

    # Admin widzi wszystkie zespoły
    if current_user.system_role == SystemRole.ADMIN:
        result = await db.execute(
            select(Team)
            .where(Team.is_active.is_(True))
            .offset(skip)
            .limit(limit)
        )
        teams = result.scalars().all()
        total = await db.scalar(
            select(func.count(Team.id)).where(Team.is_active.is_(True))
        )
    else:
        # Zwykli użytkownicy - tylko zespoły w których są członkami
        result = await db.execute(
            select(Team)
            .join(TeamMembership, TeamMembership.team_id == Team.id)
            .where(
                Team.is_active.is_(True),
                TeamMembership.user_id == current_user.id,
            )
            .offset(skip)
            .limit(limit)
        )
        teams = result.scalars().all()
        total = await db.scalar(
            select(func.count(Team.id))
            .join(TeamMembership, TeamMembership.team_id == Team.id)
            .where(
                Team.is_active.is_(True),
                TeamMembership.user_id == current_user.id,
            )
        )

    return TeamListResponse(teams=teams, total=total)


@router.get("/teams/{team_id}", response_model=TeamResponse, tags=["Teams"])
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pobierz szczegóły zespołu

    Zwraca szczegółowe informacje o zespole włącznie z listą członków
    i licznikami (member_count, project_count).

    Args:
        team_id: UUID zespołu
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Szczegóły zespołu z członkami

    Raises:
        HTTPException 404: Jeśli zespół nie istnieje lub użytkownik nie ma dostępu
    """
    team = await get_team_for_user(team_id, current_user, db)

    # Pobierz liczniki
    member_count = await db.scalar(
        select(func.count(TeamMembership.id)).where(
            TeamMembership.team_id == team_id
        )
    )

    project_count = await db.scalar(
        select(func.count(Project.id)).where(
            Project.team_id == team_id,
            Project.is_active.is_(True),
        )
    )

    # Pobierz członków zespołu z danymi użytkowników
    result = await db.execute(
        select(TeamMembership, User)
        .join(User, TeamMembership.user_id == User.id)
        .where(TeamMembership.team_id == team_id)
        .order_by(TeamMembership.created_at)
    )
    rows = result.all()

    members = [
        TeamMemberInfo(
            user_id=membership.user_id,
            email=user.email,
            full_name=user.full_name,
            role_in_team=membership.role_in_team,
            joined_at=membership.created_at,
        )
        for membership, user in rows
    ]

    # Przygotuj odpowiedź
    team_response = TeamResponse.model_validate(team)
    team_response.member_count = member_count
    team_response.project_count = project_count
    team_response.members = members

    return team_response


@router.put("/teams/{team_id}", response_model=TeamResponse, tags=["Teams"])
async def update_team(
    team_id: UUID,
    team_update: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Zaktualizuj zespół

    Tylko właściciele zespołu (OWNER) mogą aktualizować zespół.

    Args:
        team_id: UUID zespołu do aktualizacji
        team_update: Nowe wartości pól (wszystkie opcjonalne)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Zaktualizowany zespół

    Raises:
        HTTPException 404: Jeśli zespół nie istnieje lub użytkownik nie ma dostępu
        HTTPException 403: Jeśli użytkownik nie jest właścicielem zespołu
    """
    # Sprawdź czy użytkownik jest właścicielem
    membership = await require_team_membership(
        team_id, current_user, db,
        allowed_roles=[TeamRole.OWNER]
    )

    team = await get_team_for_user(team_id, current_user, db)

    # Aktualizuj tylko podane pola
    update_data = team_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)

    logger.info(
        "Team updated",
        extra={
            "team_id": str(team_id),
            "updated_by": str(current_user.id),
            "updated_fields": list(update_data.keys()),
        }
    )

    return team


@router.delete("/teams/{team_id}", status_code=204, tags=["Teams"])
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń zespół (soft delete)

    Tylko właściciele zespołu (OWNER) mogą usuwać zespół.
    Usunięcie zespołu powoduje:
    - Soft delete zespołu (is_active = False)
    - Usunięcie wszystkich projektów zespołu (cascade)
    - Usunięcie wszystkich członków zespołu (cascade)

    Args:
        team_id: UUID zespołu do usunięcia
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Raises:
        HTTPException 404: Jeśli zespół nie istnieje lub użytkownik nie ma dostępu
        HTTPException 403: Jeśli użytkownik nie jest właścicielem zespołu
    """
    # Sprawdź czy użytkownik jest właścicielem
    membership = await require_team_membership(
        team_id, current_user, db,
        allowed_roles=[TeamRole.OWNER]
    )

    team = await get_team_for_user(team_id, current_user, db)

    # Soft delete
    team.is_active = False

    await db.commit()

    logger.info(
        "Team deleted (soft delete)",
        extra={
            "team_id": str(team_id),
            "deleted_by": str(current_user.id),
        }
    )


@router.post("/teams/{team_id}/members", response_model=TeamMembershipResponse, status_code=201, tags=["Teams"])
async def add_team_member(
    team_id: UUID,
    membership: TeamMembershipCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Dodaj członka do zespołu

    Tylko właściciele zespołu (OWNER) mogą dodawać członków.

    Args:
        team_id: UUID zespołu
        membership: Dane członka (user_id lub email, role_in_team)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Utworzone członkostwo z timestampem

    Raises:
        HTTPException 404: Jeśli zespół lub użytkownik nie istnieje
        HTTPException 403: Jeśli użytkownik nie jest właścicielem zespołu
        HTTPException 409: Jeśli użytkownik jest już członkiem zespołu
    """
    # Sprawdź czy użytkownik jest właścicielem
    await require_team_membership(
        team_id, current_user, db,
        allowed_roles=[TeamRole.OWNER]
    )

    # Znajdź użytkownika do dodania
    if membership.user_id:
        result = await db.execute(
            select(User).where(User.id == membership.user_id)
        )
        user_to_add = result.scalar_one_or_none()
    elif membership.email:
        result = await db.execute(
            select(User).where(User.email == membership.email)
        )
        user_to_add = result.scalar_one_or_none()
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either user_id or email must be provided"
        )

    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Sprawdź czy użytkownik nie jest już członkiem
    existing_membership = await db.scalar(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_to_add.id,
        )
    )

    if existing_membership:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this team"
        )

    # Dodaj członka
    db_membership = TeamMembership(
        team_id=team_id,
        user_id=user_to_add.id,
        role_in_team=membership.role_in_team,
    )

    db.add(db_membership)
    await db.commit()
    await db.refresh(db_membership)

    logger.info(
        "Member added to team",
        extra={
            "team_id": str(team_id),
            "user_id": str(user_to_add.id),
            "role": membership.role_in_team.value,
            "added_by": str(current_user.id),
        }
    )

    # Przygotuj odpowiedź z dodatkowymi danymi
    response = TeamMembershipResponse.model_validate(db_membership)
    response.user_email = user_to_add.email
    response.user_full_name = user_to_add.full_name

    return response


@router.put("/teams/{team_id}/members/{user_id}", response_model=TeamMembershipResponse, tags=["Teams"])
async def update_team_member_role(
    team_id: UUID,
    user_id: UUID,
    membership_update: TeamMembershipUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Zaktualizuj rolę członka zespołu

    Tylko właściciele zespołu (OWNER) mogą zmieniać role członków.

    Args:
        team_id: UUID zespołu
        user_id: UUID użytkownika
        membership_update: Nowa rola (role_in_team)
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Returns:
        Zaktualizowane członkostwo

    Raises:
        HTTPException 404: Jeśli zespół lub członek nie istnieje
        HTTPException 403: Jeśli użytkownik nie jest właścicielem zespołu
    """
    # Sprawdź czy użytkownik jest właścicielem
    await require_team_membership(
        team_id, current_user, db,
        allowed_roles=[TeamRole.OWNER]
    )

    # Znajdź członkostwo
    result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team membership not found"
        )

    # Aktualizuj rolę
    membership.role_in_team = membership_update.role_in_team

    await db.commit()
    await db.refresh(membership)

    logger.info(
        "Team member role updated",
        extra={
            "team_id": str(team_id),
            "user_id": str(user_id),
            "new_role": membership_update.role_in_team.value,
            "updated_by": str(current_user.id),
        }
    )

    return membership


@router.delete("/teams/{team_id}/members/{user_id}", status_code=204, tags=["Teams"])
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Usuń członka z zespołu

    Tylko właściciele zespołu (OWNER) mogą usuwać członków.
    Nie można usunąć ostatniego właściciela zespołu.

    Args:
        team_id: UUID zespołu
        user_id: UUID użytkownika do usunięcia
        db: Sesja bazy danych
        current_user: Zalogowany użytkownik

    Raises:
        HTTPException 404: Jeśli zespół lub członek nie istnieje
        HTTPException 403: Jeśli użytkownik nie jest właścicielem zespołu
        HTTPException 400: Jeśli próba usunięcia ostatniego właściciela
    """
    # Sprawdź czy użytkownik jest właścicielem
    await require_team_membership(
        team_id, current_user, db,
        allowed_roles=[TeamRole.OWNER]
    )

    # Znajdź członkostwo
    result = await db.execute(
        select(TeamMembership).where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == user_id,
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team membership not found"
        )

    # Sprawdź czy to nie ostatni właściciel
    if membership.role_in_team == TeamRole.OWNER:
        owner_count = await db.scalar(
            select(func.count(TeamMembership.id)).where(
                TeamMembership.team_id == team_id,
                TeamMembership.role_in_team == TeamRole.OWNER,
            )
        )

        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner of the team. Assign another owner first."
            )

    # Usuń członka
    await db.delete(membership)
    await db.commit()

    logger.info(
        "Member removed from team",
        extra={
            "team_id": str(team_id),
            "user_id": str(user_id),
            "removed_by": str(current_user.id),
        }
    )
