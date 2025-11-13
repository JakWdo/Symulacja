"""
API Endpoints dla Environments i Saved Filters (Shared Context)

Obsługuje:
- Zarządzanie environments (team-level workspaces)
- Filtrowanie zasobów w environments (DSL queries)
- Zapisywanie i zarządzanie filtrami DSL
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Environment, Team, SavedFilter, User
from app.api.dependencies import get_current_user, require_team_membership
from app.services.filters.query_builder import filter_resources, QueryBuilderError
from pydantic import BaseModel, Field


router = APIRouter(prefix="/environments", tags=["environments"])


# === Schemas ===

class EnvironmentCreate(BaseModel):
    """Schema dla tworzenia environment."""
    team_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class EnvironmentResponse(BaseModel):
    """Schema dla response environment."""
    id: UUID
    team_id: UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class FilterResourcesRequest(BaseModel):
    """Schema dla request filtrowania zasobów."""
    dsl: str = Field(..., description="DSL query (np. 'dem:age-25-34 AND geo:warsaw')")
    resource_type: str = Field(..., description="Typ zasobu (persona, workflow)")
    limit: int = Field(100, ge=1, le=1000, description="Limit wyników")
    cursor: Optional[str] = Field(None, description="Kursor dla paginacji")


class FilterResourcesResponse(BaseModel):
    """Schema dla response filtrowania zasobów."""
    resource_ids: List[UUID]
    next_cursor: Optional[str] = None
    count: int


class SavedFilterCreate(BaseModel):
    """Schema dla tworzenia saved filter."""
    environment_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    dsl: str = Field(..., description="DSL query")


class SavedFilterResponse(BaseModel):
    """Schema dla response saved filter."""
    id: UUID
    environment_id: UUID
    name: str
    dsl: str
    created_by: Optional[UUID] = None
    created_at: str

    class Config:
        from_attributes = True


# === Endpoints: Environments ===

@router.post("", response_model=EnvironmentResponse, status_code=201)
async def create_environment(
    data: EnvironmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tworzy nowe environment dla zespołu.

    Wymaga:
    - Użytkownik musi być członkiem zespołu (owner lub member)
    """
    # Sprawdź czy user jest członkiem teamu
    await require_team_membership(data.team_id, ["owner", "member"], current_user, db)

    # Sprawdź czy team istnieje
    team_result = await db.execute(
        select(Team).where(and_(Team.id == data.team_id, Team.is_active == True))
    )
    team = team_result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Utwórz environment
    environment = Environment(
        team_id=data.team_id,
        name=data.name,
        description=data.description,
    )

    db.add(environment)
    await db.commit()
    await db.refresh(environment)

    return environment


@router.get("", response_model=List[EnvironmentResponse])
async def list_environments(
    team_id: Optional[UUID] = Query(None, description="Filtruj po team_id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Listuje environments dostępne dla użytkownika.

    Zwraca environments dla wszystkich teamów użytkownika (lub wyfiltrowane po team_id).
    """
    # Pobierz user z team_memberships
    user_result = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.team_memberships))
    )
    user = user_result.scalar_one()

    # Zbierz team_ids użytkownika
    user_team_ids = [membership.team_id for membership in user.team_memberships]

    # Filtruj environments
    query = select(Environment).where(
        and_(
            Environment.team_id.in_(user_team_ids),
            Environment.is_active == True,
        )
    )

    if team_id:
        # Sprawdź czy user jest w tym teamie
        if team_id not in user_team_ids:
            raise HTTPException(status_code=403, detail="Access denied to this team")
        query = query.where(Environment.team_id == team_id)

    result = await db.execute(query.order_by(Environment.created_at.desc()))
    environments = result.scalars().all()

    return environments


@router.get("/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(
    environment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pobiera szczegóły environment.

    Wymaga:
    - Użytkownik musi być członkiem teamu environment
    """
    # Pobierz environment
    result = await db.execute(
        select(Environment).where(
            and_(Environment.id == environment_id, Environment.is_active == True)
        )
    )
    environment = result.scalar_one_or_none()

    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Sprawdź czy user jest członkiem teamu
    await require_team_membership(environment.team_id, ["owner", "member", "viewer"], current_user, db)

    return environment


@router.post("/{environment_id}/filter", response_model=FilterResourcesResponse)
async def filter_environment_resources(
    environment_id: UUID,
    filter_request: FilterResourcesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Filtruje zasoby w environment używając DSL query.

    Wymaga:
    - Użytkownik musi być członkiem teamu environment
    - DSL query musi być poprawny

    Przykłady DSL:
    - "dem:age-25-34 AND geo:warsaw"
    - "(psy:high-openness OR psy:high-extraversion) AND NOT dem:age-55-plus"
    """
    # Pobierz environment i sprawdź dostęp
    result = await db.execute(
        select(Environment).where(
            and_(Environment.id == environment_id, Environment.is_active == True)
        )
    )
    environment = result.scalar_one_or_none()

    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Sprawdź czy user jest członkiem teamu
    await require_team_membership(environment.team_id, ["owner", "member", "viewer"], current_user, db)

    # Wykonaj filtrowanie
    try:
        resource_ids = await filter_resources(
            db=db,
            dsl=filter_request.dsl,
            resource_type=filter_request.resource_type,
            environment_id=environment_id,
            limit=filter_request.limit,
            cursor=filter_request.cursor,
        )
    except QueryBuilderError as e:
        raise HTTPException(status_code=400, detail=f"Invalid DSL query: {e}")

    # Ustal next_cursor (ostatni resource_id jeśli osiągnięto limit)
    next_cursor = None
    if len(resource_ids) == filter_request.limit:
        next_cursor = str(resource_ids[-1])

    return FilterResourcesResponse(
        resource_ids=resource_ids,
        next_cursor=next_cursor,
        count=len(resource_ids),
    )


# === Endpoints: Saved Filters ===

@router.post("/filters", response_model=SavedFilterResponse, status_code=201, tags=["saved-filters"])
async def create_saved_filter(
    data: SavedFilterCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Tworzy nowy saved filter.

    Wymaga:
    - Użytkownik musi być członkiem teamu environment
    """
    # Sprawdź czy environment istnieje i user ma dostęp
    result = await db.execute(
        select(Environment).where(
            and_(Environment.id == data.environment_id, Environment.is_active == True)
        )
    )
    environment = result.scalar_one_or_none()

    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Sprawdź czy user jest członkiem teamu
    await require_team_membership(environment.team_id, ["owner", "member"], current_user, db)

    # Utwórz saved filter
    saved_filter = SavedFilter(
        environment_id=data.environment_id,
        name=data.name,
        dsl=data.dsl,
        created_by=current_user.id,
    )

    db.add(saved_filter)
    await db.commit()
    await db.refresh(saved_filter)

    return saved_filter


@router.get("/filters", response_model=List[SavedFilterResponse], tags=["saved-filters"])
async def list_saved_filters(
    environment_id: UUID = Query(..., description="Environment ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Listuje saved filters dla environment.

    Wymaga:
    - Użytkownik musi być członkiem teamu environment
    """
    # Sprawdź czy environment istnieje i user ma dostęp
    result = await db.execute(
        select(Environment).where(
            and_(Environment.id == environment_id, Environment.is_active == True)
        )
    )
    environment = result.scalar_one_or_none()

    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Sprawdź czy user jest członkiem teamu
    await require_team_membership(environment.team_id, ["owner", "member", "viewer"], current_user, db)

    # Pobierz saved filters
    filters_result = await db.execute(
        select(SavedFilter)
        .where(SavedFilter.environment_id == environment_id)
        .order_by(SavedFilter.created_at.desc())
    )
    filters = filters_result.scalars().all()

    return filters


@router.get("/filters/{filter_id}", response_model=SavedFilterResponse, tags=["saved-filters"])
async def get_saved_filter(
    filter_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Pobiera szczegóły saved filter.

    Wymaga:
    - Użytkownik musi być członkiem teamu environment
    """
    # Pobierz filter
    result = await db.execute(
        select(SavedFilter).where(SavedFilter.id == filter_id)
    )
    saved_filter = result.scalar_one_or_none()

    if not saved_filter:
        raise HTTPException(status_code=404, detail="Saved filter not found")

    # Sprawdź dostęp przez environment
    env_result = await db.execute(
        select(Environment).where(Environment.id == saved_filter.environment_id)
    )
    environment = env_result.scalar_one_or_none()

    if not environment:
        raise HTTPException(status_code=404, detail="Environment not found")

    # Sprawdź czy user jest członkiem teamu
    await require_team_membership(environment.team_id, ["owner", "member", "viewer"], current_user, db)

    return saved_filter
