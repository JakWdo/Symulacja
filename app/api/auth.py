"""
Authentication endpoints: register, login, logout, me

Endpointy odpowiedzialne za autentykację użytkowników.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import get_settings
from app.db.session import get_db
from app.api.dependencies import get_current_user
import re

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)


# === SCHEMAS ===
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company: Optional[str] = None
    role: Optional[str] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Za-z]', v) or not re.search(r'\d', v):
            raise ValueError('Password must contain letters and numbers')
        if len(v.encode("utf-8")) > 72:
            raise ValueError('Password must be at most 72 bytes')
        return v

    @validator('full_name')
    def validate_name(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: Optional[str]
    company: Optional[str]
    avatar_url: Optional[str]
    plan: str
    is_verified: bool
    created_at: str

    class Config:
        from_attributes = True


# === ENDPOINTS ===
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Rejestracja nowego użytkownika"""

    # Sprawdź czy email już istnieje
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Utwórz nowego użytkownika
    new_user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        company=request.company,
        role=request.role,
        plan="free",
        is_verified=False,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generuj JWT token
    access_token = create_access_token(
        data={"sub": str(new_user.id), "email": new_user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "company": new_user.company,
            "plan": new_user.plan,
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Logowanie użytkownika"""

    # Znajdź użytkownika po emailu
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    # Weryfikuj dane logowania
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Zaktualizuj znacznik czasu ostatniego logowania
    user.last_login_at = datetime.utcnow()

    try:
        await db.commit()
    except SQLAlchemyError as exc:
        # W środowiskach z nieaktualnym schematem bazy (np. brak kolumny last_login_at)
        # commit może się nie powieść. Zamiast zwracać 500, wycofujemy transakcję i
        # kontynuujemy logowanie – użytkownik otrzyma token, a informacja o
        # ostatnim logowaniu po prostu nie zostanie zapisana.
        await db.rollback()
        logger.warning("Nie udało się zapisać last_login_at podczas logowania: %s", exc)

    # Generuj JWT token
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "company": user.company,
            "avatar_url": user.avatar_url,
            "plan": user.plan,
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Pobierz informacje o zalogowanym użytkowniku"""

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company": current_user.company,
        "avatar_url": current_user.avatar_url,
        "plan": current_user.plan,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at.isoformat(),
    }


@router.post("/logout")
async def logout():
    """
    Logout użytkownika

    Backend jest stateless (JWT), więc logout jest obsługiwany po stronie frontend
    (usunięcie tokenu z localStorage). Ten endpoint istnieje dla spójności API.
    """
    return {"message": "Logged out successfully"}
