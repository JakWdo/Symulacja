"""
LLM Settings API Endpoints

Endpoints dla zarządzania preferencjami LLM provider i modeli.
Wspiera user-level preferences i project-level overrides.
"""
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["llm-settings"])


# ============================================================================
# Pydantic Schemas
# ============================================================================

class LLMProvider(str):
    """Enum-like dla LLM providers (dla validation)"""
    GOOGLE = "google"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class UserLLMSettingsResponse(BaseModel):
    """Response schema dla user LLM settings"""
    preferred_llm_provider: Optional[str] = Field(None, description="User preferred provider")
    preferred_model: Optional[str] = Field(None, description="User preferred model")
    available_providers: list[str] = Field(
        default_factory=lambda: ["google", "openai", "anthropic", "azure_openai"],
        description="List of supported providers"
    )


class UserLLMSettingsUpdate(BaseModel):
    """Request schema dla update user LLM settings"""
    preferred_llm_provider: Optional[str] = Field(
        None,
        description="Preferred LLM provider (google, openai, anthropic, azure_openai)"
    )
    preferred_model: Optional[str] = Field(
        None,
        description="Preferred model (e.g., gemini-2.5-flash, gpt-4o, claude-3-5-sonnet)"
    )


class ProjectLLMSettingsResponse(BaseModel):
    """Response schema dla project LLM settings"""
    llm_provider_override: Optional[str] = Field(None, description="Project-specific provider")
    model_override: Optional[str] = Field(None, description="Project-specific model")
    effective_provider: str = Field(..., description="Effective provider (resolved from overrides)")
    effective_model: Optional[str] = Field(None, description="Effective model (resolved)")


class ProjectLLMSettingsUpdate(BaseModel):
    """Request schema dla update project LLM settings"""
    llm_provider_override: Optional[str] = Field(
        None,
        description="Override provider for this project (NULL = use user/system default)"
    )
    model_override: Optional[str] = Field(
        None,
        description="Override model for this project (NULL = use provider default)"
    )


# ============================================================================
# User LLM Settings Endpoints
# ============================================================================

@router.get("/users/me/llm-settings", response_model=UserLLMSettingsResponse)
async def get_user_llm_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Pobierz LLM settings dla zalogowanego użytkownika.

    Returns:
        User preferred provider i model
    """
    return UserLLMSettingsResponse(
        preferred_llm_provider=current_user.preferred_llm_provider,
        preferred_model=current_user.preferred_model,
    )


@router.put("/users/me/llm-settings", response_model=UserLLMSettingsResponse)
async def update_user_llm_settings(
    settings: UserLLMSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Zaktualizuj LLM settings dla zalogowanego użytkownika.

    Args:
        settings: Nowe ustawienia LLM

    Returns:
        Zaktualizowane settings
    """
    # Validate provider
    valid_providers = ["google", "openai", "anthropic", "azure_openai"]
    if settings.preferred_llm_provider and settings.preferred_llm_provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Must be one of: {valid_providers}"
        )

    # Update user settings
    if settings.preferred_llm_provider is not None:
        current_user.preferred_llm_provider = settings.preferred_llm_provider

    if settings.preferred_model is not None:
        current_user.preferred_model = settings.preferred_model

    await db.commit()
    await db.refresh(current_user)

    logger.info(
        f"Updated LLM settings for user {current_user.id}: "
        f"provider={current_user.preferred_llm_provider}, "
        f"model={current_user.preferred_model}"
    )

    return UserLLMSettingsResponse(
        preferred_llm_provider=current_user.preferred_llm_provider,
        preferred_model=current_user.preferred_model,
    )


# ============================================================================
# Project LLM Settings Endpoints
# ============================================================================

@router.get("/projects/{project_id}/llm-settings", response_model=ProjectLLMSettingsResponse)
async def get_project_llm_settings(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Pobierz LLM settings dla projektu.

    Args:
        project_id: ID projektu

    Returns:
        Project LLM settings + effective (resolved) provider/model
    """
    # Fetch project
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found or access denied"
        )

    # Resolve effective provider (priority: project > user > system default)
    effective_provider = (
        project.llm_provider_override
        or current_user.preferred_llm_provider
        or "google"  # System default
    )

    # Resolve effective model (priority: project > user > provider default)
    effective_model = (
        project.model_override
        or current_user.preferred_model
        or None  # Will be resolved by config.models.yaml
    )

    return ProjectLLMSettingsResponse(
        llm_provider_override=project.llm_provider_override,
        model_override=project.model_override,
        effective_provider=effective_provider,
        effective_model=effective_model,
    )


@router.put("/projects/{project_id}/llm-settings", response_model=ProjectLLMSettingsResponse)
async def update_project_llm_settings(
    project_id: UUID,
    settings: ProjectLLMSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Zaktualizuj LLM settings dla projektu.

    Args:
        project_id: ID projektu
        settings: Nowe ustawienia LLM

    Returns:
        Zaktualizowane settings + effective provider/model
    """
    # Fetch project
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found or access denied"
        )

    # Validate provider
    valid_providers = ["google", "openai", "anthropic", "azure_openai"]
    if settings.llm_provider_override and settings.llm_provider_override not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Must be one of: {valid_providers}"
        )

    # Update project settings
    if settings.llm_provider_override is not None:
        project.llm_provider_override = settings.llm_provider_override

    if settings.model_override is not None:
        project.model_override = settings.model_override

    await db.commit()
    await db.refresh(project)

    # Resolve effective settings
    effective_provider = (
        project.llm_provider_override
        or current_user.preferred_llm_provider
        or "google"
    )

    effective_model = (
        project.model_override
        or current_user.preferred_model
        or None
    )

    logger.info(
        f"Updated LLM settings for project {project_id}: "
        f"provider_override={project.llm_provider_override}, "
        f"model_override={project.model_override}, "
        f"effective_provider={effective_provider}"
    )

    return ProjectLLMSettingsResponse(
        llm_provider_override=project.llm_provider_override,
        model_override=project.model_override,
        effective_provider=effective_provider,
        effective_model=effective_model,
    )
