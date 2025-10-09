"""
User settings endpoints (simplified version)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.models.project import Project
from app.models.persona import Persona
from app.db.session import get_db
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


# === SCHEMAS ===
class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None


class UpdateNotificationsRequest(BaseModel):
    email_notifications_enabled: Optional[bool] = None
    discussion_complete_notifications: Optional[bool] = None
    weekly_reports_enabled: Optional[bool] = None
    system_updates_notifications: Optional[bool] = None


class AccountStatsResponse(BaseModel):
    plan: str
    projects_count: int
    personas_count: int
    focus_groups_count: int


# === ENDPOINTS ===
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Pobierz profil użytkownika"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company": current_user.company,
        "avatar_url": current_user.avatar_url,
        "plan": current_user.plan,
        "created_at": current_user.created_at.isoformat(),
    }


@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Zaktualizuj profil użytkownika"""
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.role is not None:
        current_user.role = request.role
    if request.company is not None:
        current_user.company = request.company

    await db.commit()
    await db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": str(current_user.id),
            "full_name": current_user.full_name,
            "role": current_user.role,
            "company": current_user.company,
        }
    }


@router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Pobierz ustawienia notyfikacji"""
    return {
        "email_notifications_enabled": current_user.email_notifications_enabled,
        "discussion_complete_notifications": current_user.discussion_complete_notifications,
        "weekly_reports_enabled": current_user.weekly_reports_enabled,
        "system_updates_notifications": current_user.system_updates_notifications,
    }


@router.put("/notifications")
async def update_notifications(
    request: UpdateNotificationsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Zaktualizuj ustawienia notyfikacji"""
    if request.email_notifications_enabled is not None:
        current_user.email_notifications_enabled = request.email_notifications_enabled
    if request.discussion_complete_notifications is not None:
        current_user.discussion_complete_notifications = request.discussion_complete_notifications
    if request.weekly_reports_enabled is not None:
        current_user.weekly_reports_enabled = request.weekly_reports_enabled
    if request.system_updates_notifications is not None:
        current_user.system_updates_notifications = request.system_updates_notifications

    await db.commit()

    return {"message": "Notification settings updated successfully"}


@router.get("/stats", response_model=AccountStatsResponse)
async def get_account_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pobierz statystyki konta"""

    # Policz projekty
    projects_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.owner_id == current_user.id,
            Project.is_active == True
        )
    )
    projects_count = projects_result.scalar()

    # Policz persony (poprzez projekty)
    personas_result = await db.execute(
        select(func.count(Persona.id))
        .join(Project, Persona.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    personas_count = personas_result.scalar()

    # Policz grupy fokusowe
    from app.models.focus_group import FocusGroup
    fg_result = await db.execute(
        select(func.count(FocusGroup.id))
        .join(Project, FocusGroup.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    focus_groups_count = fg_result.scalar()

    return {
        "plan": current_user.plan,
        "projects_count": projects_count,
        "personas_count": personas_count,
        "focus_groups_count": focus_groups_count,
    }


@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Usuń konto użytkownika (soft delete)"""
    from datetime import datetime

    # Miękkie usunięcie użytkownika
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False

    # Miękkie usunięcie wszystkich projektów
    result = await db.execute(
        select(Project).where(
            Project.owner_id == current_user.id,
            Project.is_active == True
        )
    )
    projects = result.scalars().all()

    for project in projects:
        project.is_active = False

    await db.commit()

    return {"message": "Account deleted successfully"}
