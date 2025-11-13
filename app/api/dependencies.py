"""
FastAPI dependencies dla autentykacji i autoryzacji

Ten moduł zawiera dependency functions używane w endpointach API:
- get_current_user: Weryfikuje JWT token i zwraca zalogowanego użytkownika
- get_current_active_user: Dodatkowo sprawdza czy konto jest aktywne
- get_current_admin_user: Wymaga uprawnień administratora

Użycie w endpointach:
    @router.get("/protected")
    async def protected_route(current_user: User = Depends(get_current_user)):
        return {"user_id": current_user.id}
"""
from uuid import UUID
import logging

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import decode_access_token
from app.models.user import User, SystemRole
from app.models.project import Project
from app.models.persona import Persona
from app.models.focus_group import FocusGroup
from app.models.survey import Survey
from app.models.team import Team, TeamMembership, TeamRole
from app.db.session import get_db

# Mechanizm HTTPBearer — wymagaj nagłówka "Authorization: Bearer <token>"
security = HTTPBearer()
logger = logging.getLogger(__name__)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency do pobierania aktualnie zalogowanego użytkownika z JWT tokenu

    Flow:
    1. Wyciąga token z Authorization header
    2. Dekoduje i waliduje JWT token
    3. Pobiera użytkownika z bazy danych
    4. Sprawdza czy użytkownik istnieje i nie jest usunięty
    5. Sprawdza czy konto jest aktywne

    Args:
        credentials: HTTPAuthorizationCredentials z FastAPI security
        db: Sesja bazy danych (dependency injection)

    Returns:
        User object zalogowanego użytkownika

    Raises:
        HTTPException 401: Jeśli token jest nieprawidłowy, wygasły lub użytkownik nie istnieje
        HTTPException 403: Jeśli konto użytkownika jest nieaktywne

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}
    """
    token = credentials.credentials

    # Dekoduj i zwaliduj JWT token
    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Authentication failed: Invalid or expired JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Wyciągnij user_id z payload (zapisany jako "sub" podczas create_access_token)
    user_id: str = payload.get("sub")
    if user_id is None:
        logger.warning("Authentication failed: Token payload missing 'sub' field")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Pobierz użytkownika z bazy danych
    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None)  # Ignoruj rekordy oznaczone jako usunięte
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        logger.warning(
            "Authentication failed: User not found",
            extra={"user_id": user_id}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sprawdź czy konto jest aktywne
    if not user.is_active:
        logger.warning(
            "Authorization failed: User account disabled",
            extra={"user_id": str(user.id), "email": user.email}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    request.state.current_user = user

    logger.debug("User authenticated successfully", extra={"user_id": str(user.id)})
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency zapewniające że użytkownik jest aktywny (not disabled)

    To jest dodatkowa warstwa na get_current_user. Można używać jako
    bardziej eksplicytny sposób sprawdzania czy konto jest aktywne.

    Args:
        current_user: User z get_current_user dependency

    Returns:
        User object (zawsze aktywny)

    Raises:
        HTTPException 403: Jeśli konto jest nieaktywne

    Usage:
        @router.post("/sensitive-action")
        async def sensitive_action(current_user: User = Depends(get_current_active_user)):
            # Mamy pewność że konto jest aktywne
            pass
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency dla endpointów wymagających uprawnień administratora

    Sprawdza czy użytkownik ma system_role = ADMIN.
    Używaj dla operacji administracyjnych (np. zarządzanie wszystkimi użytkownikami).

    Args:
        current_user: User z get_current_user dependency

    Returns:
        User object z uprawnieniami admin

    Raises:
        HTTPException 403: Jeśli użytkownik nie ma uprawnień admin

    Usage:
        @router.get("/admin/users")
        async def list_all_users(current_user: User = Depends(get_current_admin_user)):
            # Tylko administratorzy mogą uzyskać dostęp
            pass
    """
    if current_user.system_role != SystemRole.ADMIN:
        logger.warning(
            "Admin access denied",
            extra={
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "user_role": current_user.system_role.value
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def get_current_researcher_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency dla endpointów wymagających uprawnień researcher lub wyższych.

    Sprawdza czy użytkownik ma system_role >= RESEARCHER (ADMIN lub RESEARCHER).
    Używaj dla operacji tworzenia/edycji projektów, person, grup fokusowych.

    Args:
        current_user: User z get_current_user dependency

    Returns:
        User object z uprawnieniami researcher+

    Raises:
        HTTPException 403: Jeśli użytkownik ma tylko rolę VIEWER

    Usage:
        @router.post("/projects")
        async def create_project(current_user: User = Depends(get_current_researcher_user)):
            # RESEARCHER i ADMIN mogą tworzyć projekty
            pass
    """
    if current_user.system_role == SystemRole.VIEWER:
        logger.warning(
            "Researcher access denied - user is VIEWER",
            extra={
                "user_id": str(current_user.id),
                "user_email": current_user.email,
                "user_role": current_user.system_role.value
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Researcher access required (view-only users cannot perform this action)"
        )
    return current_user


# Opcjonalna zależność dla publicznych endpointów (token jest opcjonalny)
async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    Dependency zwracające użytkownika jeśli jest zalogowany, None w przeciwnym razie

    Użyteczne dla endpointów które zachowują się inaczej dla zalogowanych vs niezalogowanych.
    Przykład: publiczna strona główna która pokazuje personalizowaną treść gdy zalogowany.

    Args:
        request: FastAPI Request object
        db: Sesja bazy danych

    Returns:
        User object jeśli zalogowany, None jeśli nie

    Usage:
        @router.get("/")
        async def homepage(current_user: Optional[User] = Depends(get_current_user_optional)):
            if current_user:
                return {"message": f"Welcome back, {current_user.full_name}"}
            return {"message": "Welcome, guest"}
    """
    # Wyciągnij token bezpośrednio z request.headers
    authorization = request.headers.get("authorization")

    logger.debug(f"get_current_user_optional called, authorization header: {authorization}")

    if not authorization:
        logger.debug("No authorization header, returning None")
        return None

    # Wyciągnij token z nagłówka "Bearer <token>"
    if not authorization.startswith("Bearer "):
        logger.debug("Invalid authorization header format, returning None")
        return None

    try:
        token = authorization.replace("Bearer ", "", 1)
        payload = decode_access_token(token)
        if payload is None:
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        result = await db.execute(
            select(User).where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if user and user.is_active:
            request.state.current_user = user
            return user
    except Exception:
        # Ignorujemy błędy i zwracamy None dla dostępu publicznego
        pass

    return None


async def get_project_for_user(
    project_id: UUID,
    current_user: User,
    db: AsyncSession,
    *,
    include_inactive: bool = False,
) -> Project:
    """
    Pobierz projekt do którego użytkownik ma dostęp lub zwróć 404.

    Dostęp mają:
    1. Admin (pełny dostęp do wszystkich projektów)
    2. Członkowie teamu do którego należy projekt (przez team_id)
    3. Właściciel projektu (legacy support dla projektów bez team_id)

    Args:
        project_id: UUID projektu
        current_user: Zalogowany użytkownik
        db: Sesja bazy danych
        include_inactive: Czy uwzględnić nieaktywne projekty

    Returns:
        Project object jeśli użytkownik ma dostęp

    Raises:
        HTTPException 404: Jeśli projekt nie istnieje lub użytkownik nie ma dostępu
    """
    # Admin ma dostęp do wszystkich projektów
    if current_user.system_role == SystemRole.ADMIN:
        conditions = [Project.id == project_id]
        if not include_inactive:
            conditions.append(Project.is_active.is_(True))

        result = await db.execute(select(Project).where(*conditions))
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

        return project

    # Zwykli użytkownicy - sprawdź team membership lub ownership
    # Projekt jest dostępny jeśli:
    # 1. user jest członkiem teamu projektu (team_id is not None i user ∈ team)
    # 2. user jest właścicielem projektu (owner_id = user_id) - legacy
    from sqlalchemy import or_, and_

    conditions = [Project.id == project_id]
    if not include_inactive:
        conditions.append(Project.is_active.is_(True))

    # Warunek dostępu: owner LUB member teamu
    access_condition = or_(
        Project.owner_id == current_user.id,  # Legacy: właściciel
        and_(
            Project.team_id.isnot(None),  # Projekt ma team
            Project.team_id.in_(  # User jest członkiem tego teamu
                select(TeamMembership.team_id).where(
                    TeamMembership.user_id == current_user.id
                )
            )
        )
    )
    conditions.append(access_condition)

    result = await db.execute(select(Project).where(*conditions))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return project


async def get_persona_for_user(
    persona_id: UUID,
    current_user: User,
    db: AsyncSession,
    include_inactive: bool = False,
) -> Persona:
    """
    Pobierz personę, do której użytkownik ma dostęp (poprzez projekt), lub zwróć 404.

    Dostęp poprzez projekt - sprawdza membership w teamie projektu lub ownership.
    """
    from sqlalchemy import or_, and_

    # Admin ma dostęp do wszystkich person
    if current_user.system_role == SystemRole.ADMIN:
        conditions = [
            Persona.id == persona_id,
            Project.is_active.is_(True),
        ]
        if not include_inactive:
            conditions.append(Persona.is_active.is_(True))
            conditions.append(Persona.deleted_at.is_(None))

        result = await db.execute(
            select(Persona)
            .join(Project, Persona.project_id == Project.id)
            .where(*conditions)
        )
        persona = result.scalar_one_or_none()

        if not persona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")

        return persona

    # Zwykli użytkownicy - sprawdź dostęp przez team lub ownership
    access_condition = or_(
        Project.owner_id == current_user.id,  # Legacy: właściciel projektu
        and_(
            Project.team_id.isnot(None),  # Projekt ma team
            Project.team_id.in_(  # User jest członkiem tego teamu
                select(TeamMembership.team_id).where(
                    TeamMembership.user_id == current_user.id
                )
            )
        )
    )

    conditions = [
        Persona.id == persona_id,
        Project.is_active.is_(True),
        access_condition,
    ]
    if not include_inactive:
        conditions.append(Persona.is_active.is_(True))
        conditions.append(Persona.deleted_at.is_(None))

    result = await db.execute(
        select(Persona)
        .join(Project, Persona.project_id == Project.id)
        .where(*conditions)
    )
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")

    return persona


async def get_focus_group_for_user(
    focus_group_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> FocusGroup:
    """
    Pobierz grupę fokusową należącą do projektu użytkownika lub zwróć 404.

    Dostęp poprzez projekt - sprawdza membership w teamie projektu lub ownership.
    """
    from sqlalchemy import or_, and_

    logger.debug(
        "Checking focus group access",
        extra={
            "focus_group_id": str(focus_group_id),
            "user_id": str(current_user.id),
        }
    )

    # Admin ma dostęp do wszystkich grup fokusowych
    if current_user.system_role == SystemRole.ADMIN:
        result = await db.execute(
            select(FocusGroup)
            .join(Project, FocusGroup.project_id == Project.id)
            .where(
                FocusGroup.id == focus_group_id,
                Project.is_active.is_(True),
            )
        )
        focus_group = result.scalar_one_or_none()

        if not focus_group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus group not found")

        return focus_group

    # Zwykli użytkownicy - sprawdź dostęp przez team lub ownership
    access_condition = or_(
        Project.owner_id == current_user.id,  # Legacy: właściciel projektu
        and_(
            Project.team_id.isnot(None),  # Projekt ma team
            Project.team_id.in_(  # User jest członkiem tego teamu
                select(TeamMembership.team_id).where(
                    TeamMembership.user_id == current_user.id
                )
            )
        )
    )

    result = await db.execute(
        select(FocusGroup)
        .join(Project, FocusGroup.project_id == Project.id)
        .where(
            FocusGroup.id == focus_group_id,
            Project.is_active.is_(True),
            access_condition,
        )
    )
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        logger.warning(
            "Focus group not found or access denied",
            extra={
                "focus_group_id": str(focus_group_id),
                "user_id": str(current_user.id),
                "reason": "Either focus group doesn't exist, user doesn't have access to project, or project is inactive"
            }
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus group not found")

    logger.debug(
        "Focus group access granted",
        extra={
            "focus_group_id": str(focus_group_id),
            "user_id": str(current_user.id),
            "project_id": str(focus_group.project_id),
        }
    )

    return focus_group


async def get_survey_for_user(
    survey_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Survey:
    """
    Pobierz ankietę powiązaną z projektem użytkownika lub zwróć 404.

    Dostęp poprzez projekt - sprawdza membership w teamie projektu lub ownership.
    """
    from sqlalchemy import or_, and_

    # Admin ma dostęp do wszystkich ankiet
    if current_user.system_role == SystemRole.ADMIN:
        result = await db.execute(
            select(Survey)
            .join(Project, Survey.project_id == Project.id)
            .where(
                Survey.id == survey_id,
                Survey.is_active.is_(True),
                Project.is_active.is_(True),
            )
        )
        survey = result.scalar_one_or_none()

        if not survey:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

        return survey

    # Zwykli użytkownicy - sprawdź dostęp przez team lub ownership
    access_condition = or_(
        Project.owner_id == current_user.id,  # Legacy: właściciel projektu
        and_(
            Project.team_id.isnot(None),  # Projekt ma team
            Project.team_id.in_(  # User jest członkiem tego teamu
                select(TeamMembership.team_id).where(
                    TeamMembership.user_id == current_user.id
                )
            )
        )
    )

    result = await db.execute(
        select(Survey)
        .join(Project, Survey.project_id == Project.id)
        .where(
            Survey.id == survey_id,
            Survey.is_active.is_(True),
            Project.is_active.is_(True),
            access_condition,
        )
    )
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    return survey


# ============================================================================
# TEAM MEMBERSHIP DEPENDENCIES
# ============================================================================


async def get_team_for_user(
    team_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Team:
    """
    Pobierz team do którego użytkownik ma dostęp lub zwróć 404.

    Sprawdza czy użytkownik jest członkiem teamu (przez TeamMembership).
    Admin ma dostęp do wszystkich teamów.

    Args:
        team_id: UUID teamu
        current_user: Zalogowany użytkownik
        db: Sesja bazy danych

    Returns:
        Team object jeśli użytkownik ma dostęp

    Raises:
        HTTPException 404: Jeśli team nie istnieje lub użytkownik nie ma dostępu
    """
    # Admin ma dostęp do wszystkich teamów
    if current_user.system_role == SystemRole.ADMIN:
        result = await db.execute(
            select(Team).where(
                Team.id == team_id,
                Team.is_active.is_(True),
            )
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        return team

    # Zwykli użytkownicy - sprawdź membership
    result = await db.execute(
        select(Team)
        .join(TeamMembership, TeamMembership.team_id == Team.id)
        .where(
            Team.id == team_id,
            Team.is_active.is_(True),
            TeamMembership.user_id == current_user.id,
        )
    )
    team = result.scalar_one_or_none()

    if not team:
        logger.warning(
            "Team not found or access denied",
            extra={
                "team_id": str(team_id),
                "user_id": str(current_user.id),
                "reason": "Either team doesn't exist, is inactive, or user is not a member"
            }
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    return team


async def require_team_membership(
    team_id: UUID,
    current_user: User,
    db: AsyncSession,
    allowed_roles: list[TeamRole] | None = None,
) -> TeamMembership:
    """
    Dependency wymuszające że użytkownik należy do teamu z określonymi rolami.

    Sprawdza:
    1. Czy użytkownik jest członkiem teamu
    2. Czy ma jedną z dozwolonych ról w teamie
    3. Admin ma zawsze dostęp (traktowany jako OWNER)

    Args:
        team_id: UUID teamu
        current_user: Zalogowany użytkownik
        db: Sesja bazy danych
        allowed_roles: Lista dozwolonych ról (None = wszystkie role OK)

    Returns:
        TeamMembership object użytkownika w teamie

    Raises:
        HTTPException 404: Jeśli team nie istnieje lub użytkownik nie jest członkiem
        HTTPException 403: Jeśli użytkownik ma niewystarczającą rolę w teamie

    Usage:
        @router.post("/teams/{team_id}/projects")
        async def create_project_in_team(
            team_id: UUID,
            current_user: User = Depends(get_current_user),
            db: AsyncSession = Depends(get_db),
        ):
            # Tylko owner i member mogą tworzyć projekty
            membership = await require_team_membership(
                team_id, current_user, db,
                allowed_roles=[TeamRole.OWNER, TeamRole.MEMBER]
            )
            # ... logika tworzenia projektu
    """
    # Admin ma zawsze pełny dostęp (traktowany jako owner)
    if current_user.system_role == SystemRole.ADMIN:
        # Sprawdź czy team istnieje
        result = await db.execute(
            select(Team).where(
                Team.id == team_id,
                Team.is_active.is_(True),
            )
        )
        team = result.scalar_one_or_none()

        if not team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

        # Zwróć "wirtualny" membership dla admina (nie zapisujemy go do bazy)
        # Potrzebujemy tylko dla celów logicznych, nie persistence
        logger.debug(
            "Admin access granted to team",
            extra={"team_id": str(team_id), "user_id": str(current_user.id)}
        )
        # Tworzymy obiekt membership bez zapisu do bazy (transient object)
        from uuid import uuid4
        virtual_membership = TeamMembership(
            id=uuid4(),
            team_id=team_id,
            user_id=current_user.id,
            role_in_team=TeamRole.OWNER  # Admin = owner
        )
        return virtual_membership

    # Zwykli użytkownicy - pobierz membership z bazy
    result = await db.execute(
        select(TeamMembership)
        .join(Team, TeamMembership.team_id == Team.id)
        .where(
            TeamMembership.team_id == team_id,
            TeamMembership.user_id == current_user.id,
            Team.is_active.is_(True),
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        logger.warning(
            "Team membership not found",
            extra={
                "team_id": str(team_id),
                "user_id": str(current_user.id),
                "reason": "User is not a member of this team or team is inactive"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this team"
        )

    # Sprawdź czy użytkownik ma wymaganą rolę
    if allowed_roles is not None and membership.role_in_team not in allowed_roles:
        logger.warning(
            "Insufficient team role",
            extra={
                "team_id": str(team_id),
                "user_id": str(current_user.id),
                "user_role": membership.role_in_team.value,
                "required_roles": [r.value for r in allowed_roles]
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required roles: {', '.join(r.value for r in allowed_roles)}"
        )

    logger.debug(
        "Team membership validated",
        extra={
            "team_id": str(team_id),
            "user_id": str(current_user.id),
            "role": membership.role_in_team.value
        }
    )

    return membership
