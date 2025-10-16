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
from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import decode_access_token
from app.models.user import User
from app.models.project import Project
from app.models.persona import Persona
from app.models.focus_group import FocusGroup
from app.models.survey import Survey
from app.db.session import get_db

# Mechanizm HTTPBearer — wymagaj nagłówka "Authorization: Bearer <token>"
security = HTTPBearer()


async def get_current_user(
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Wyciągnij user_id z payload (zapisany jako "sub" podczas create_access_token)
    user_id: str = payload.get("sub")
    if user_id is None:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Sprawdź czy konto jest aktywne
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

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

    Sprawdza czy użytkownik ma plan "enterprise" (lub w przyszłości dodaj pole is_admin).
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
    # DO ZROBIENIA: w przyszłości dodaj pole User.is_admin zamiast sprawdzania planu
    if current_user.plan != "enterprise":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


# Opcjonalna zależność dla publicznych endpointów (token jest opcjonalny)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency zwracające użytkownika jeśli jest zalogowany, None w przeciwnym razie

    Użyteczne dla endpointów które zachowują się inaczej dla zalogowanych vs niezalogowanych.
    Przykład: publiczna strona główna która pokazuje personalizowaną treść gdy zalogowany.

    Args:
        credentials: Opcjonalne credentials (może być None)
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
    if credentials is None:
        return None

    try:
        token = credentials.credentials
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
    Pobierz projekt należący do aktualnego użytkownika lub zwróć 404.
    """
    conditions = [
        Project.id == project_id,
        Project.owner_id == current_user.id,
    ]
    if not include_inactive:
        conditions.append(Project.is_active.is_(True))

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
    """
    conditions = [
        Persona.id == persona_id,
        Project.owner_id == current_user.id,
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


async def get_focus_group_for_user(
    focus_group_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> FocusGroup:
    """
    Pobierz grupę fokusową należącą do projektu użytkownika lub zwróć 404.
    """
    result = await db.execute(
        select(FocusGroup)
        .join(Project, FocusGroup.project_id == Project.id)
        .where(
            FocusGroup.id == focus_group_id,
            Project.owner_id == current_user.id,
            Project.is_active.is_(True),
        )
    )
    focus_group = result.scalar_one_or_none()

    if not focus_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Focus group not found")

    return focus_group


async def get_survey_for_user(
    survey_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> Survey:
    """
    Pobierz ankietę powiązaną z projektem użytkownika lub zwróć 404.
    """
    result = await db.execute(
        select(Survey)
        .join(Project, Survey.project_id == Project.id)
        .where(
            Survey.id == survey_id,
            Survey.is_active.is_(True),
            Project.owner_id == current_user.id,
            Project.is_active.is_(True),
        )
    )
    survey = result.scalar_one_or_none()

    if not survey:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey not found")

    return survey
