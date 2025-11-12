"""
Admin endpoints: user management, project management, system configuration

Endpointy administracyjne wymagające roli ADMIN.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import User, SystemRole
from app.models.project import Project
from app.db.session import get_db
from app.api.dependencies import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = logging.getLogger(__name__)


# === SCHEMAS ===
class UserListResponse(BaseModel):
    """Response dla listy użytkowników"""
    id: str
    email: str
    full_name: str
    system_role: str
    plan: str
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class UpdateUserRoleRequest(BaseModel):
    """Request do zmiany roli użytkownika"""
    system_role: SystemRole


# === ENDPOINTS ===
@router.get("/users", response_model=list[UserListResponse])
async def list_all_users(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista wszystkich użytkowników systemu.

    **Wymaga:** Rola ADMIN

    Returns:
        Lista użytkowników z ich rolami i statusem
    """
    result = await db.execute(
        select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    logger.info(
        "Admin listed all users",
        extra={
            "admin_id": str(current_user.id),
            "admin_email": current_user.email,
            "total_users": len(users)
        }
    )

    return [
        {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "system_role": user.system_role.value,
            "plan": user.plan,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
        }
        for user in users
    ]


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: UUID,
    request: UpdateUserRoleRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Zmień rolę systemową użytkownika.

    **Wymaga:** Rola ADMIN

    Args:
        user_id: UUID użytkownika
        request: Nowa rola systemowa

    Returns:
        Zaktualizowane dane użytkownika
    """
    # Pobierz użytkownika
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Nie pozwól administratorom usunąć własnej roli admin (ostatnia linia obrony)
    if user.id == current_user.id and request.system_role != SystemRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin role"
        )

    # Zaktualizuj rolę
    old_role = user.system_role
    user.system_role = request.system_role
    await db.commit()
    await db.refresh(user)

    logger.info(
        "Admin changed user role",
        extra={
            "admin_id": str(current_user.id),
            "admin_email": current_user.email,
            "target_user_id": str(user.id),
            "target_user_email": user.email,
            "old_role": old_role.value,
            "new_role": user.system_role.value
        }
    )

    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "system_role": user.system_role.value,
        "message": f"Role updated from {old_role.value} to {user.system_role.value}"
    }


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: UUID,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Usuń projekt (twardo, nie soft-delete).

    **Wymaga:** Rola ADMIN

    Uwaga: To jest trwałe usunięcie! Używaj z ostrożnością.

    Args:
        project_id: UUID projektu do usunięcia

    Returns:
        Potwierdzenie usunięcia
    """
    # Pobierz projekt
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Usuń projekt (twardo)
    project_name = project.name
    project_owner_id = project.owner_id

    await db.delete(project)
    await db.commit()

    logger.warning(
        "Admin deleted project",
        extra={
            "admin_id": str(current_user.id),
            "admin_email": current_user.email,
            "project_id": str(project_id),
            "project_name": project_name,
            "project_owner_id": str(project_owner_id),
            "action": "hard_delete"
        }
    )

    return {
        "message": f"Project '{project_name}' deleted successfully",
        "project_id": str(project_id)
    }


@router.get("/stats")
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Statystyki systemu.

    **Wymaga:** Rola ADMIN

    Returns:
        Podstawowe statystyki użytkowników, projektów, itp.
    """
    from sqlalchemy import func
    from app.models.persona import Persona
    from app.models.focus_group import FocusGroup

    # Zlicz użytkowników
    total_users = await db.scalar(
        select(func.count(User.id)).where(User.deleted_at.is_(None))
    )
    active_users = await db.scalar(
        select(func.count(User.id)).where(
            User.deleted_at.is_(None),
            User.is_active.is_(True)
        )
    )

    # Zlicz projekty
    total_projects = await db.scalar(
        select(func.count(Project.id)).where(Project.deleted_at.is_(None))
    )
    active_projects = await db.scalar(
        select(func.count(Project.id)).where(
            Project.deleted_at.is_(None),
            Project.is_active.is_(True)
        )
    )

    # Zlicz persony
    total_personas = await db.scalar(
        select(func.count(Persona.id)).where(Persona.deleted_at.is_(None))
    )

    # Zlicz grupy fokusowe
    total_focus_groups = await db.scalar(
        select(func.count(FocusGroup.id)).where(FocusGroup.deleted_at.is_(None))
    )

    # Role breakdown
    role_counts = {}
    for role in SystemRole:
        count = await db.scalar(
            select(func.count(User.id)).where(
                User.deleted_at.is_(None),
                User.system_role == role
            )
        )
        role_counts[role.value] = count or 0

    logger.info(
        "Admin viewed system stats",
        extra={
            "admin_id": str(current_user.id),
            "admin_email": current_user.email
        }
    )

    return {
        "users": {
            "total": total_users or 0,
            "active": active_users or 0,
            "by_role": role_counts
        },
        "projects": {
            "total": total_projects or 0,
            "active": active_projects or 0
        },
        "personas": {
            "total": total_personas or 0
        },
        "focus_groups": {
            "total": total_focus_groups or 0
        }
    }
