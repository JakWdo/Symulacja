"""
Settings endpoints: profile, avatar upload, account stats

Endpointy do zarządzania ustawieniami użytkownika i kontem.
Wszystkie wymagają uwierzytelnienia JWT.
"""
import asyncio
import io
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.focus_group import FocusGroup
from app.models.persona import Persona
from app.models.project import Project
from app.models.survey import Survey
from app.models.user import User
from app.schemas.settings import (
    AccountStatsResponse,
    AvatarUploadResponse,
    BudgetSettingsResponse,
    BudgetSettingsUpdateRequest,
    MessageResponse,
    ProfileResponse,
    ProfileUpdateRequest,
)
try:
    import aiofiles  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback for environments without aiofiles
    aiofiles = None
logger = logging.getLogger(__name__)


class _AsyncFileWrapper:
    """Minimal async context manager when aiofiles is unavailable."""

    def __init__(self, path: str | Path, mode: str, *args, **kwargs):
        self._path = path
        self._mode = mode
        self._args = args
        self._kwargs = kwargs
        self._file = None

    async def __aenter__(self):
        self._file = open(self._path, self._mode, *self._args, **self._kwargs)
        return self

    async def write(self, data):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._file.write, data)

    async def __aexit__(self, exc_type, exc, tb):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._file.close)


def _open_async(path: str | Path, mode: str, *args, **kwargs):
    if aiofiles is not None:
        return aiofiles.open(path, mode, *args, **kwargs)
    return _AsyncFileWrapper(path, mode, *args, **kwargs)

settings = get_settings()
router = APIRouter(prefix="/settings", tags=["Settings"])

# Konfiguracja upload avatarów
AVATAR_DIR = Path("static/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}


# === PROFILE ENDPOINTS ===
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Pobierz pełny profil zalogowanego użytkownika

    Returns:
        Szczegółowy profil z wszystkimi informacjami
    """
    return ProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        company=current_user.company,
        avatar_url=current_user.avatar_url,
        plan=current_user.plan,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat(),
        last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
    )


@router.put("/profile", response_model=MessageResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Zaktualizuj profil użytkownika

    Args:
        request: Dane do aktualizacji (full_name, role, company)

    Returns:
        Wiadomość o sukcesie i zaktualizowany profil
    """
    # Aktualizuj tylko podane pola
    if request.full_name is not None:
        current_user.full_name = request.full_name
    if request.role is not None:
        current_user.role = request.role
    if request.company is not None:
        current_user.company = request.company

    current_user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(current_user)

    return MessageResponse(
        message="Profile updated successfully",
        user=ProfileResponse(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            company=current_user.company,
            avatar_url=current_user.avatar_url,
            plan=current_user.plan,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at.isoformat(),
            last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        )
    )


# === BUDGET SETTINGS ENDPOINTS ===
@router.get("/budget", response_model=BudgetSettingsResponse)
async def get_budget_settings(
    current_user: User = Depends(get_current_user)
):
    """
    Pobierz ustawienia budżetu zalogowanego użytkownika

    Returns:
        Ustawienia budżetu (limit, warning/critical thresholds)
    """
    return BudgetSettingsResponse(
        budget_limit=current_user.budget_limit,
        warning_threshold=current_user.warning_threshold or 80,
        critical_threshold=current_user.critical_threshold or 90,
    )


@router.put("/budget", response_model=BudgetSettingsResponse)
async def update_budget_settings(
    request: BudgetSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Zaktualizuj ustawienia budżetu użytkownika

    Args:
        request: Dane do aktualizacji (budget_limit, warning_threshold, critical_threshold)

    Returns:
        Zaktualizowane ustawienia budżetu
    """
    # Aktualizuj tylko podane pola
    if request.budget_limit is not None:
        current_user.budget_limit = request.budget_limit
    if request.warning_threshold is not None:
        current_user.warning_threshold = request.warning_threshold
    if request.critical_threshold is not None:
        current_user.critical_threshold = request.critical_threshold

    current_user.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(current_user)

    return BudgetSettingsResponse(
        budget_limit=current_user.budget_limit,
        warning_threshold=current_user.warning_threshold or 80,
        critical_threshold=current_user.critical_threshold or 90,
    )


# === AVATAR ENDPOINTS ===
@router.post("/avatar", response_model=AvatarUploadResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload avatara użytkownika

    Args:
        file: Plik obrazu (JPG, PNG, WEBP, max 2MB)

    Returns:
        URL do uploadowanego avatara
    """
    # Walidacja typu pliku
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_AVATAR_TYPES)}"
        )

    # Odczytaj zawartość pliku
    contents = await file.read()

    # Walidacja rozmiaru
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_AVATAR_SIZE / 1024 / 1024}MB"
        )

    # Walidacja że to prawidłowy obraz
    try:
        image = Image.open(io.BytesIO(contents))
        image.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file"
        )

    # Usuń stary avatar jeśli istnieje
    if current_user.avatar_url:
        old_avatar_path = Path(current_user.avatar_url.lstrip('/'))
        # Security: Waliduj że path jest wewnątrz AVATAR_DIR (ochrona przed path traversal)
        try:
            old_avatar_path = old_avatar_path.resolve()
            avatar_dir_resolved = AVATAR_DIR.resolve()
            if not str(old_avatar_path).startswith(str(avatar_dir_resolved)):
                logger.warning(
                    "Attempt to delete file outside avatar directory: %s",
                    current_user.avatar_url
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid avatar path"
                )
            if old_avatar_path.exists():
                old_avatar_path.unlink()
        except (ValueError, OSError) as e:
            logger.error("Error deleting old avatar: %s", e)
            # Kontynuuj nawet jeśli usunięcie się nie powiodło

    # Generuj unikalną nazwę pliku
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
    file_path = AVATAR_DIR / unique_filename

    # Zapisz plik
    async with _open_async(file_path, 'wb') as f:
        await f.write(contents)

    # Zaktualizuj URL w bazie
    avatar_url = f"/static/avatars/{unique_filename}"
    current_user.avatar_url = avatar_url
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    return AvatarUploadResponse(
        message="Avatar uploaded successfully",
        avatar_url=avatar_url
    )


@router.delete("/avatar", response_model=MessageResponse)
async def delete_avatar(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Usuń avatar użytkownika

    Returns:
        Wiadomość o sukcesie
    """
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No avatar to delete"
        )

    # Usuń plik z dysku
    avatar_path = Path(current_user.avatar_url.lstrip('/'))
    # Security: Waliduj że path jest wewnątrz AVATAR_DIR (ochrona przed path traversal)
    try:
        avatar_path = avatar_path.resolve()
        avatar_dir_resolved = AVATAR_DIR.resolve()
        if not str(avatar_path).startswith(str(avatar_dir_resolved)):
            logger.warning(
                "Attempt to delete file outside avatar directory: %s",
                current_user.avatar_url
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid avatar path"
            )
        if avatar_path.exists():
            avatar_path.unlink()
    except (ValueError, OSError) as e:
        logger.error("Error deleting avatar file: %s", e)
        # Kontynuuj - usuń URL z bazy nawet jeśli plik nie został usunięty

    # Usuń URL z bazy
    current_user.avatar_url = None
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    return MessageResponse(message="Avatar deleted successfully")


# === ACCOUNT STATS ENDPOINT ===
@router.get("/stats", response_model=AccountStatsResponse)
async def get_account_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pobierz statystyki konta użytkownika

    Returns:
        Liczba projektów, person, grup fokusowych, ankiet
    """
    # Count projektów
    projects_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.owner_id == current_user.id,
            Project.is_active.is_(True),
        )
    )
    projects_count = projects_result.scalar() or 0

    # Count person (poprzez projekty)
    personas_result = await db.execute(
        select(func.count(Persona.id))
        .join(Project, Persona.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    personas_count = personas_result.scalar() or 0

    # Count grup fokusowych
    focus_groups_result = await db.execute(
        select(func.count(FocusGroup.id))
        .join(Project, FocusGroup.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    focus_groups_count = focus_groups_result.scalar() or 0

    # Count ankiet
    surveys_result = await db.execute(
        select(func.count(Survey.id))
        .join(Project, Survey.project_id == Project.id)
        .where(Project.owner_id == current_user.id)
    )
    surveys_count = surveys_result.scalar() or 0

    return AccountStatsResponse(
        plan=current_user.plan,
        projects_count=projects_count,
        personas_count=personas_count,
        focus_groups_count=focus_groups_count,
        surveys_count=surveys_count,
    )


# === ACCOUNT DELETION ENDPOINT ===
@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Usuń konto użytkownika (soft delete)

    Returns:
        Wiadomość o sukcesie

    Note:
        To jest soft delete - konto jest oznaczane jako usunięte (deleted_at)
        ale dane pozostają w bazie dla compliance i audytu.
        Użytkownik nie będzie mógł się zalogować.
    """
    # Soft delete - ustaw deleted_at
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False
    current_user.updated_at = datetime.utcnow()

    await db.commit()

    return MessageResponse(message="Account deleted successfully")
