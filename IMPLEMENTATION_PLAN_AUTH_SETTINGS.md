# Plan Implementacji: System Logowania + Panel Settings

**Data:** 2025-10-09
**Projekt:** Market Research SaaS
**Zakres:** Kompletny system autentykacji użytkowników + funkcjonalny panel Settings

---

## 📋 Spis Treści

1. [Przegląd Systemu](#1-przegląd-systemu)
2. [Architektura Systemu Logowania](#2-architektura-systemu-logowania)
3. [Interface Ładowania Aplikacji](#3-interface-ładowania-aplikacji)
4. [Model Użytkownika (Backend)](#4-model-użytkownika-backend)
5. [System Autentykacji JWT (Backend)](#5-system-autentykacji-jwt-backend)
6. [Endpoints API (Backend)](#6-endpoints-api-backend)
7. [Frontend - Auth Flow](#7-frontend---auth-flow)
8. [Panel Settings (Frontend)](#8-panel-settings-frontend)
9. [Integracja z Istniejącym Kodem](#9-integracja-z-istniejącym-kodem)
10. [Bezpieczeństwo](#10-bezpieczeństwo)
11. [Kolejność Implementacji](#11-kolejność-implementacji)
12. [Struktura Plików](#12-struktura-plików)

---

## 1. Przegląd Systemu

### 1.1 Obecny Stan
- ❌ Brak systemu autentykacji
- ❌ Brak modelu User w bazie danych
- ❌ Panel Settings jest mock-upem (nie zapisuje danych)
- ✅ Theme system działa (localStorage)
- ✅ Design system gotowy (Tailwind + shadcn/ui)

### 1.2 Cel Implementacji
Stworzenie kompletnego systemu umożliwiającego:
- **Rejestrację** nowych użytkowników
- **Logowanie** z emailem + hasłem
- **JWT authentication** dla zabezpieczenia API
- **Loading screen** podczas inicjalizacji aplikacji
- **Funkcjonalny panel Settings** z:
  - Edycją profilu
  - Zarządzaniem API key (Google Gemini)
  - Ustawieniami notyfikacji
  - Statystykami konta
  - Upload avatara

### 1.3 Stack Technologiczny
**Backend:**
- FastAPI (istniejące)
- PostgreSQL + SQLAlchemy async
- JWT tokens (python-jose)
- Passlib (bcrypt dla haseł)
- Cryptography (Fernet dla API keys)

**Frontend:**
- React 18 + TypeScript
- TanStack Query (React Query)
- Zustand (state management)
- shadcn/ui components

---

## 2. Architektura Systemu Logowania

### 2.1 Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION START                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │   Loading Screen      │  ← Animowany logo + spinner
                │   (AppLoader.tsx)     │
                └───────────────────────┘
                            ↓
              Check localStorage token
                            ↓
                ┌───────────┴───────────┐
                │                       │
           Token exists?           No token
                │                       │
                ↓                       ↓
    ┌──────────────────┐      ┌────────────────┐
    │ Validate token   │      │  Login Screen  │
    │ GET /auth/me     │      │  (Login.tsx)   │
    └──────────────────┘      └────────────────┘
                │                       │
         Valid? │                       │
                │                       ↓
        ┌───────┴──────┐       ┌────────────────┐
        ↓              ↓       │ POST /auth/    │
   ✅ Valid      ❌ Invalid   │   login        │
        │              │       └────────────────┘
        │              │                │
        │              └────────────────┤
        ↓                               ↓
┌────────────────┐              Receive JWT token
│  Main App      │              Save to localStorage
│  (Dashboard)   │              Redirect to Dashboard
└────────────────┘                      ↓
        │                        ┌────────────────┐
        │                        │   Main App     │
        └────────────────────────│  (Dashboard)   │
                                 └────────────────┘
```

### 2.2 Token Management
- **Access Token:** JWT, krótki TTL (30 min), przechowywany w localStorage
- **Refresh Token:** Opcjonalny (future enhancement), dłuższy TTL (7 dni)
- **Token Structure:**
  ```json
  {
    "user_id": "uuid",
    "email": "user@example.com",
    "exp": 1234567890,
    "iat": 1234567890
  }
  ```

### 2.3 Protected Routes
Wszystkie endpointy API będą wymagały autentykacji:
- `/api/v1/projects/*` → Wymaga JWT
- `/api/v1/personas/*` → Wymaga JWT
- `/api/v1/focus-groups/*` → Wymaga JWT
- `/api/v1/settings/*` → Wymaga JWT

**Wyjątki (publiczne):**
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /health`

---

## 3. Interface Ładowania Aplikacji

### 3.1 Component: AppLoader.tsx

**Lokalizacja:** `frontend/src/components/AppLoader.tsx`

**Design:**
- Pełnoekranowy overlay z gradientem
- Animowany logo (spinning) w centrum
- Progress bar lub pulsujący tekst
- Smooth fade-out transition

**Implementacja:**
```tsx
// frontend/src/components/AppLoader.tsx
import { Logo } from '@/components/ui/Logo';
import { cn } from '@/lib/utils';

interface AppLoaderProps {
  message?: string;
}

export function AppLoader({ message = "Loading..." }: AppLoaderProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-background via-background to-sidebar">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute w-96 h-96 -top-48 -left-48 bg-brand-orange/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute w-96 h-96 -bottom-48 -right-48 bg-chart-1/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* Content */}
      <div className="relative flex flex-col items-center gap-8">
        {/* Logo with spinning animation */}
        <div className="relative">
          <Logo
            spinning
            transparent
            className="w-20 h-20"
          />
          {/* Glow effect ring */}
          <div className="absolute inset-0 rounded-full bg-brand-orange/20 blur-xl animate-glow" />
        </div>

        {/* Loading text */}
        <div className="flex flex-col items-center gap-2">
          <p className="text-lg font-medium text-foreground">{message}</p>

          {/* Animated dots */}
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-brand-orange rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-brand-orange rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-brand-orange rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        </div>

        {/* Progress bar (optional) */}
        <div className="w-64 h-1 bg-muted rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-brand-orange to-chart-1 animate-[shimmer_2s_ease-in-out_infinite]" />
        </div>
      </div>
    </div>
  );
}

// Add shimmer animation to tailwind.config.js:
// shimmer: {
//   '0%': { transform: 'translateX(-100%)' },
//   '100%': { transform: 'translateX(100%)' }
// }
```

### 3.2 Kiedy Pokazywać Loader

1. **Initial App Load:** Podczas sprawdzania tokenu i pobierania danych użytkownika
2. **Login/Register:** Podczas wysyłania credentials do API
3. **Token Refresh:** Podczas odświeżania sesji (future)

**Nie pokazywać przy:**
- Nawigacji między stronami (użyj lokalnych spinnerów)
- Ładowaniu danych w tle (użyj skeleton screens)

---

## 4. Model Użytkownika (Backend)

### 4.1 Database Model

**Plik:** `app/models/user.py`

```python
"""
Model użytkownika z pełnym wsparciem dla autentykacji i ustawień
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.models.base import Base


class User(Base):
    """
    Użytkownik systemu z autentykacją i ustawieniami

    Relacje:
    - projects: Lista projektów należących do użytkownika (1:N)
    - personas: Wszystkie persony utworzone przez użytkownika (poprzez projekty)
    """
    __tablename__ = "users"

    # === PODSTAWOWE INFORMACJE ===
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # === PROFIL ===
    full_name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)  # np. "Market Researcher", "Product Manager"
    company = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)  # URL do avatara

    # === API CONFIGURATION ===
    # Szyfrowany Google API key (używany zamiast globalnego)
    encrypted_google_api_key = Column(Text, nullable=True)

    # === NOTIFICATION SETTINGS ===
    email_notifications_enabled = Column(Boolean, default=True)
    discussion_complete_notifications = Column(Boolean, default=True)
    weekly_reports_enabled = Column(Boolean, default=False)
    system_updates_notifications = Column(Boolean, default=True)

    # === ACCOUNT STATUS ===
    is_active = Column(Boolean, default=True)  # Account enabled/disabled
    is_verified = Column(Boolean, default=False)  # Email verified (future)
    plan = Column(String(50), default="free")  # "free", "pro", "enterprise"

    # === TIMESTAMPS ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # === RELATIONSHIPS ===
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"
```

### 4.2 Update Project Model

**Plik:** `app/models/project.py` (modyfikacja)

```python
# Dodaj kolumnę owner_id:
owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

# Dodaj relationship:
owner = relationship("User", back_populates="projects")
```

### 4.3 Alembic Migration

**Plik:** `alembic/versions/XXXX_create_users_table.py`

```python
"""create users table and add owner to projects

Revision ID: XXXX
Create Date: 2025-10-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(100), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('encrypted_google_api_key', sa.Text, nullable=True),
        sa.Column('email_notifications_enabled', sa.Boolean, default=True),
        sa.Column('discussion_complete_notifications', sa.Boolean, default=True),
        sa.Column('weekly_reports_enabled', sa.Boolean, default=False),
        sa.Column('system_updates_notifications', sa.Boolean, default=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('plan', sa.String(50), default='free'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime, nullable=True),
        sa.Column('deleted_at', sa.DateTime, nullable=True),
    )

    # Create index on email
    op.create_index('idx_users_email', 'users', ['email'])

    # Add owner_id to projects table
    op.add_column('projects', sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True))

    # Create default user (dla istniejących projektów)
    conn = op.get_bind()
    default_user_id = str(uuid.uuid4())
    conn.execute(f"""
        INSERT INTO users (id, email, hashed_password, full_name, plan, created_at, updated_at)
        VALUES (
            '{default_user_id}',
            'admin@example.com',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lkqKmLqHvzGK',  -- hasło: "changeme"
            'Default Admin',
            'enterprise',
            NOW(),
            NOW()
        )
    """)

    # Przypisz istniejące projekty do default user
    conn.execute(f"""
        UPDATE projects SET owner_id = '{default_user_id}' WHERE owner_id IS NULL
    """)

    # Make owner_id NOT NULL
    op.alter_column('projects', 'owner_id', nullable=False)

    # Create foreign key
    op.create_foreign_key('fk_projects_owner', 'projects', 'users', ['owner_id'], ['id'])

def downgrade():
    op.drop_constraint('fk_projects_owner', 'projects', type_='foreignkey')
    op.drop_column('projects', 'owner_id')
    op.drop_index('idx_users_email', 'users')
    op.drop_table('users')
```

---

## 5. System Autentykacji JWT (Backend)

### 5.1 Password Hashing Service

**Plik:** `app/core/security.py` (nowy)

```python
"""
Security utilities: hashing passwords, JWT tokens, API key encryption
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from app.core.config import get_settings

settings = get_settings()

# === PASSWORD HASHING ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


# === JWT TOKENS ===
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token

    Args:
        data: Payload to encode (typically {"sub": user_id, "email": email})
        expires_delta: Token expiration time (default: 30 minutes)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# === API KEY ENCRYPTION ===
# Generate cipher key from SECRET_KEY (must be 32 bytes for Fernet)
import hashlib
cipher_key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
cipher_suite = Fernet(cipher_key)

def encrypt_api_key(api_key: str) -> str:
    """Encrypt Google API key for storage"""
    encrypted = cipher_suite.encrypt(api_key.encode())
    return encrypted.decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt stored API key"""
    decrypted = cipher_suite.decrypt(encrypted_key.encode())
    return decrypted.decode()
```

### 5.2 Dependencies (Auth Guards)

**Plik:** `app/api/dependencies.py` (nowy)

```python
"""
FastAPI dependencies for authentication and authorization
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.security import decode_access_token
from app.models.user import User
from app.db.session import get_db

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token

    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.id}

    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user ID
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
    Dependency to ensure user is active (not disabled)

    Can be used as additional check on top of get_current_user
    """
    return current_user

# Optional: Admin-only routes
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency for admin-only routes"""
    if current_user.plan != "enterprise":  # Or add is_admin field
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
```

### 5.3 Database Session

**Plik:** `app/db/session.py` (sprawdź czy istnieje, jeśli nie - stwórz)

```python
"""
Database session management for async SQLAlchemy
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """
    Dependency function to get database session

    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            # use db
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

---

## 6. Endpoints API (Backend)

### 6.1 Auth Endpoints

**Plik:** `app/api/auth.py` (nowy)

```python
"""
Authentication endpoints: register, login, logout, me
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import get_settings
from app.db.session import get_db
from app.api.dependencies import get_current_user
import re

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


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
    """
    Register a new user account

    - **email**: Valid email address (unique)
    - **password**: Min 8 characters, must contain letters and numbers
    - **full_name**: User's full name
    - **company**: Optional company name
    - **role**: Optional job role

    Returns JWT token and user data
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        company=request.company,
        role=request.role,
        plan="free",  # Default plan
        is_verified=False,  # Require email verification (future)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate JWT token
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
    """
    Login with email and password

    Returns JWT token and user data
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == request.email, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    # Verify credentials
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

    # Update last login timestamp
    user.last_login_at = datetime.utcnow()
    await db.commit()

    # Generate JWT token
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
    """
    Get current authenticated user information

    Requires valid JWT token in Authorization header
    """
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
    Logout (client-side token removal)

    Backend is stateless (JWT), so logout is handled on frontend by removing token.
    This endpoint exists for consistency and future enhancements (token blacklist).
    """
    return {"message": "Logged out successfully"}
```

### 6.2 Settings Endpoints

**Plik:** `app/api/settings.py` (nowy)

```python
"""
User settings endpoints: profile, notifications, API keys, stats
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.models.project import Project
from app.models.persona import Persona
from app.core.security import encrypt_api_key, decrypt_api_key
from app.db.session import get_db
from app.api.dependencies import get_current_user
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/settings", tags=["Settings"])


# === SCHEMAS ===
class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None

    @validator('full_name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip() if v else None

class UpdateNotificationsRequest(BaseModel):
    email_notifications_enabled: Optional[bool] = None
    discussion_complete_notifications: Optional[bool] = None
    weekly_reports_enabled: Optional[bool] = None
    system_updates_notifications: Optional[bool] = None

class SaveApiKeyRequest(BaseModel):
    google_api_key: str

    @validator('google_api_key')
    def validate_api_key(cls, v):
        if not v.startswith('AI') or len(v) < 30:
            raise ValueError('Invalid Google API key format')
        return v

class AccountStatsResponse(BaseModel):
    plan: str
    projects_count: int
    personas_count: int
    focus_groups_count: int
    api_calls_this_month: int
    api_calls_limit: int
    storage_used_mb: float

class ApiKeyTestResponse(BaseModel):
    status: str  # "success" or "error"
    message: str
    model_tested: Optional[str] = None


# === ENDPOINTS ===
@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile information"""
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
    """Update user profile"""
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

@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload user avatar image

    - Accepts: JPG, PNG
    - Max size: 2MB
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG and PNG images are allowed"
        )

    # Validate file size (2MB)
    contents = await file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 2MB"
        )

    # Save file to static/avatars/
    avatars_dir = Path("static/avatars")
    avatars_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    filename = f"{current_user.id}_{uuid.uuid4()}.{file_extension}"
    file_path = avatars_dir / filename

    with open(file_path, "wb") as f:
        f.write(contents)

    # Update user avatar URL
    avatar_url = f"/static/avatars/{filename}"
    current_user.avatar_url = avatar_url
    await db.commit()

    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }

@router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    """Get notification settings"""
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
    """Update notification settings"""
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

@router.put("/api-key")
async def save_api_key(
    request: SaveApiKeyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save encrypted Google API key for user

    User's API key takes precedence over global GOOGLE_API_KEY
    """
    # Encrypt and save
    encrypted_key = encrypt_api_key(request.google_api_key)
    current_user.encrypted_google_api_key = encrypted_key
    await db.commit()

    return {"message": "API key saved successfully"}

@router.post("/api-key/test", response_model=ApiKeyTestResponse)
async def test_api_key(
    current_user: User = Depends(get_current_user)
):
    """
    Test user's Google API key by making a simple API call
    """
    if not current_user.encrypted_google_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No API key configured. Please save your API key first."
        )

    # Decrypt key
    api_key = decrypt_api_key(current_user.encrypted_google_api_key)

    # Test with Gemini
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=api_key,
            max_tokens=10
        )

        # Simple test call
        response = await llm.ainvoke("Hi")

        return {
            "status": "success",
            "message": "✅ API key is valid and working",
            "model_tested": "gemini-2.0-flash-exp"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ API key test failed: {str(e)}",
            "model_tested": None
        }

@router.get("/stats", response_model=AccountStatsResponse)
async def get_account_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get account statistics

    - Projects count
    - Personas generated
    - Focus groups count
    - API calls this month (placeholder)
    - Storage used (placeholder)
    """
    # Count projects
    projects_result = await db.execute(
        select(func.count(Project.id)).where(
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None)
        )
    )
    projects_count = projects_result.scalar()

    # Count personas (via projects)
    personas_result = await db.execute(
        select(func.count(Persona.id))
        .join(Project, Persona.project_id == Project.id)
        .where(
            Project.owner_id == current_user.id,
            Persona.deleted_at.is_(None)
        )
    )
    personas_count = personas_result.scalar()

    # Count focus groups
    from app.models.focus_group import FocusGroup
    fg_result = await db.execute(
        select(func.count(FocusGroup.id))
        .join(Project, FocusGroup.project_id == Project.id)
        .where(
            Project.owner_id == current_user.id,
            FocusGroup.deleted_at.is_(None)
        )
    )
    focus_groups_count = fg_result.scalar()

    # Plan limits
    plan_limits = {
        "free": {"api_calls": 1000, "storage": 100},
        "pro": {"api_calls": 10000, "storage": 1000},
        "enterprise": {"api_calls": 100000, "storage": 10000},
    }
    limits = plan_limits.get(current_user.plan, plan_limits["free"])

    return {
        "plan": current_user.plan,
        "projects_count": projects_count,
        "personas_count": personas_count,
        "focus_groups_count": focus_groups_count,
        "api_calls_this_month": 0,  # TODO: Implement API call tracking
        "api_calls_limit": limits["api_calls"],
        "storage_used_mb": 0.0,  # TODO: Implement storage tracking
    }

@router.delete("/account")
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete user account

    - Sets deleted_at timestamp
    - Soft deletes all projects, personas, focus groups
    - User data retained for 30 days (for recovery)
    """
    from datetime import datetime

    # Soft delete user
    current_user.deleted_at = datetime.utcnow()
    current_user.is_active = False

    # Soft delete all projects (cascades to personas via SQLAlchemy)
    result = await db.execute(
        select(Project).where(
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None)
        )
    )
    projects = result.scalars().all()

    for project in projects:
        project.deleted_at = datetime.utcnow()

    await db.commit()

    return {"message": "Account deleted successfully. Data will be permanently removed in 30 days."}
```

### 6.3 Update Existing Endpoints

**Modyfikacje w:** `app/api/projects.py`, `app/api/personas.py`, `app/api/focus_groups.py`, etc.

Dodaj dependency `get_current_user` do wszystkich endpointów:

```python
# PRZED:
@router.get("/projects")
async def get_projects(db: AsyncSession = Depends(get_db)):
    # ...

# PO:
from app.api.dependencies import get_current_user

@router.get("/projects")
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Filter by owner
    result = await db.execute(
        select(Project).where(
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None)
        )
    )
    projects = result.scalars().all()
    return projects
```

**Powtórz dla wszystkich endpointów.**

### 6.4 Update main.py

**Plik:** `app/main.py` (modyfikacje)

```python
# Dodaj import
from app.api import auth, settings

# Dodaj routery (PRZED innymi routerami)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Auth"])
app.include_router(settings.router, prefix=settings.API_V1_PREFIX, tags=["Settings"])

# Pozostałe routery (już są protected via dependencies)
app.include_router(projects.router, prefix=settings.API_V1_PREFIX, tags=["Projects"])
# ... etc
```

### 6.5 Static Files

**Dodaj do main.py:**

```python
from fastapi.staticfiles import StaticFiles

# Serve static files (avatars)
app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Utwórz folder:**
```bash
mkdir -p static/avatars
```

---

## 7. Frontend - Auth Flow

### 7.1 Auth Context

**Plik:** `frontend/src/contexts/AuthContext.tsx` (nowy)

```tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi, type User, type LoginCredentials, type RegisterData } from '@/lib/api';
import { toast } from '@/components/ui/Toast';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem('access_token')
  );
  const queryClient = useQueryClient();

  // Fetch current user (only if token exists)
  const { data: user, isLoading, error } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      if (!token) return null;
      try {
        return await authApi.me();
      } catch (error) {
        // Token invalid, clear it
        localStorage.removeItem('access_token');
        setToken(null);
        return null;
      }
    },
    enabled: !!token,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      toast.success('Welcome back!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Login failed');
    },
  });

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      localStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
      queryClient.invalidateQueries({ queryKey: ['auth'] });
      toast.success('Account created successfully!');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Registration failed');
    },
  });

  // Logout
  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    queryClient.clear();
    toast.info('Logged out');
  };

  const value: AuthContextType = {
    user: user || null,
    isLoading: isLoading || loginMutation.isPending || registerMutation.isPending,
    isAuthenticated: !!user,
    login: async (credentials) => {
      await loginMutation.mutateAsync(credentials);
    },
    register: async (data) => {
      await registerMutation.mutateAsync(data);
    },
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### 7.2 API Client Updates

**Plik:** `frontend/src/lib/api.ts` (rozszerzenie)

```typescript
// Add types
export interface User {
  id: string;
  email: string;
  full_name: string;
  role?: string;
  company?: string;
  avatar_url?: string;
  plan: string;
  is_verified: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  company?: string;
  role?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Add auth interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  register: async (data: RegisterData): Promise<TokenResponse> => {
    const { data: response } = await api.post<TokenResponse>('/auth/register', data);
    return response;
  },

  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const { data } = await api.post<TokenResponse>('/auth/login', credentials);
    return data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
  },

  me: async (): Promise<User> => {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },
};

// Settings API
export interface NotificationSettings {
  email_notifications_enabled: boolean;
  discussion_complete_notifications: boolean;
  weekly_reports_enabled: boolean;
  system_updates_notifications: boolean;
}

export interface AccountStats {
  plan: string;
  projects_count: number;
  personas_count: number;
  focus_groups_count: number;
  api_calls_this_month: number;
  api_calls_limit: number;
  storage_used_mb: number;
}

export const settingsApi = {
  getProfile: async (): Promise<User> => {
    const { data } = await api.get<User>('/settings/profile');
    return data;
  },

  updateProfile: async (payload: Partial<User>): Promise<User> => {
    const { data } = await api.put<User>('/settings/profile', payload);
    return data;
  },

  uploadAvatar: async (file: File): Promise<{ avatar_url: string }> => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post<{ avatar_url: string }>('/settings/avatar', formData);
    return data;
  },

  saveApiKey: async (apiKey: string): Promise<void> => {
    await api.put('/settings/api-key', { google_api_key: apiKey });
  },

  testApiKey: async (): Promise<{ status: string; message: string }> => {
    const { data } = await api.post<{ status: string; message: string }>('/settings/api-key/test');
    return data;
  },

  getNotifications: async (): Promise<NotificationSettings> => {
    const { data } = await api.get<NotificationSettings>('/settings/notifications');
    return data;
  },

  updateNotifications: async (settings: Partial<NotificationSettings>): Promise<void> => {
    await api.put('/settings/notifications', settings);
  },

  getStats: async (): Promise<AccountStats> => {
    const { data } = await api.get<AccountStats>('/settings/stats');
    return data;
  },

  deleteAccount: async (): Promise<void> => {
    await api.delete('/settings/account');
  },
};
```

### 7.3 Login Screen

**Plik:** `frontend/src/components/auth/Login.tsx` (nowy)

```tsx
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Logo } from '@/components/ui/Logo';
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Login() {
  const { login, register, isLoading } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: '',
    company: '',
    role: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isRegisterMode) {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
        company: formData.company || undefined,
        role: formData.role || undefined,
      });
    } else {
      await login({
        email: formData.email,
        password: formData.password,
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-sidebar p-4">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute w-96 h-96 -top-48 -left-48 bg-brand-orange/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute w-96 h-96 -bottom-48 -right-48 bg-chart-1/5 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-md relative z-10 shadow-float border-border">
        <CardHeader className="space-y-4 text-center">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-2xl shadow-lg overflow-hidden bg-white dark:bg-sidebar">
              <Logo className="w-full h-full object-cover" />
            </div>
          </div>
          <div>
            <CardTitle className="text-2xl font-semibold text-foreground">
              {isRegisterMode ? 'Create Account' : 'Welcome Back'}
            </CardTitle>
            <CardDescription className="text-muted-foreground">
              {isRegisterMode
                ? 'Start your market research journey'
                : 'Sign in to continue to your dashboard'
              }
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegisterMode && (
              <>
                <div>
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input
                    id="full_name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required={isRegisterMode}
                    className="mt-1"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="company">Company</Label>
                    <Input
                      id="company"
                      type="text"
                      placeholder="Acme Inc"
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor="role">Role</Label>
                    <Input
                      id="role"
                      type="text"
                      placeholder="Researcher"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      className="mt-1"
                    />
                  </div>
                </div>
              </>
            )}

            <div>
              <Label htmlFor="email">Email</Label>
              <div className="relative mt-1">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  className="pl-10"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative mt-1">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                  className="pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {isRegisterMode && (
                <p className="text-xs text-muted-foreground mt-1">
                  Min 8 characters, must contain letters and numbers
                </p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full bg-brand-orange hover:bg-brand-orange/90 text-white"
              disabled={isLoading}
            >
              {isLoading ? (
                <div className="flex items-center gap-2">
                  <Logo spinning transparent className="w-4 h-4" />
                  <span>{isRegisterMode ? 'Creating account...' : 'Signing in...'}</span>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <span>{isRegisterMode ? 'Create Account' : 'Sign In'}</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              )}
            </Button>

            <div className="text-center text-sm">
              <button
                type="button"
                onClick={() => setIsRegisterMode(!isRegisterMode)}
                className="text-brand-orange hover:underline"
              >
                {isRegisterMode
                  ? 'Already have an account? Sign in'
                  : "Don't have an account? Sign up"
                }
              </button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="absolute bottom-4 text-center text-sm text-muted-foreground">
        <p>© 2025 Market Research SaaS. All rights reserved.</p>
      </div>
    </div>
  );
}
```

### 7.4 App.tsx Refactor

**Plik:** `frontend/src/App.tsx` (modyfikacje)

```tsx
import { useAuth } from '@/contexts/AuthContext';
import { Login } from '@/components/auth/Login';
import { AppLoader } from '@/components/AppLoader';

export default function App() {
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading screen while checking auth
  if (isLoading) {
    return <AppLoader message="Loading your workspace..." />;
  }

  // Show login if not authenticated
  if (!isAuthenticated) {
    return <Login />;
  }

  // Show main app if authenticated
  return (
    <div className="h-screen bg-background text-foreground">
      <SidebarProvider className="h-full">
        {/* ... existing app content ... */}
      </SidebarProvider>
    </div>
  );
}
```

### 7.5 Main.tsx Updates

**Plik:** `frontend/src/main.tsx` (modyfikacje)

```tsx
import { AuthProvider } from '@/contexts/AuthContext';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
```

---

## 8. Panel Settings (Frontend)

### 8.1 Settings Hooks

**Plik:** `frontend/src/hooks/useSettings.ts` (nowy)

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { settingsApi, type NotificationSettings, type AccountStats } from '@/lib/api';
import { toast } from '@/components/ui/Toast';
import { useAuth } from '@/contexts/AuthContext';

export function useProfile() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['settings', 'profile'],
    queryFn: settingsApi.getProfile,
    enabled: !!user,
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success('Profile updated successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update profile');
    },
  });
}

export function useUploadAvatar() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.uploadAvatar,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'profile'] });
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] });
      toast.success('Avatar uploaded successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to upload avatar');
    },
  });
}

export function useNotifications() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['settings', 'notifications'],
    queryFn: settingsApi.getNotifications,
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useUpdateNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: settingsApi.updateNotifications,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'notifications'] });
      toast.success('Notification settings updated');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to update settings');
    },
  });
}

export function useSaveApiKey() {
  return useMutation({
    mutationFn: settingsApi.saveApiKey,
    onSuccess: () => {
      toast.success('API key saved successfully');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to save API key');
    },
  });
}

export function useTestApiKey() {
  return useMutation({
    mutationFn: settingsApi.testApiKey,
    onSuccess: (data) => {
      if (data.status === 'success') {
        toast.success(data.message);
      } else {
        toast.error(data.message);
      }
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to test API key');
    },
  });
}

export function useAccountStats() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ['settings', 'stats'],
    queryFn: settingsApi.getStats,
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useDeleteAccount() {
  const { logout } = useAuth();

  return useMutation({
    mutationFn: settingsApi.deleteAccount,
    onSuccess: () => {
      toast.success('Account deleted successfully');
      logout();
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to delete account');
    },
  });
}
```

### 8.2 Settings.tsx Refactor

**Plik:** `frontend/src/components/Settings.tsx` (duża modyfikacja)

```tsx
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
  useProfile,
  useUpdateProfile,
  useUploadAvatar,
  useNotifications,
  useUpdateNotifications,
  useSaveApiKey,
  useTestApiKey,
  useAccountStats,
  useDeleteAccount,
} from '@/hooks/useSettings';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useTheme } from '@/hooks/use-theme';
import { Key, User, Bell, Shield, Database, Eye, EyeOff, Palette, Upload } from 'lucide-react';

export function Settings() {
  const { user, logout } = useAuth();
  const { theme, setTheme } = useTheme();

  // Queries
  const { data: profile, isLoading: profileLoading } = useProfile();
  const { data: notifications, isLoading: notificationsLoading } = useNotifications();
  const { data: stats, isLoading: statsLoading } = useAccountStats();

  // Mutations
  const updateProfileMutation = useUpdateProfile();
  const uploadAvatarMutation = useUploadAvatar();
  const updateNotificationsMutation = useUpdateNotifications();
  const saveApiKeyMutation = useSaveApiKey();
  const testApiKeyMutation = useTestApiKey();
  const deleteAccountMutation = useDeleteAccount();

  // Local state
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [profileForm, setProfileForm] = useState({
    full_name: profile?.full_name || '',
    role: profile?.role || '',
    company: profile?.company || '',
  });
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Update form when profile loads
  useEffect(() => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name,
        role: profile.role || '',
        company: profile.company || '',
      });
    }
  }, [profile]);

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('Image must be less than 2MB');
      return;
    }

    await uploadAvatarMutation.mutateAsync(file);
  };

  const handleSaveProfile = async () => {
    await updateProfileMutation.mutateAsync(profileForm);
  };

  const handleSaveApiKey = async () => {
    if (!apiKey.trim()) {
      toast.error('Please enter an API key');
      return;
    }
    await saveApiKeyMutation.mutateAsync(apiKey);
    setApiKey('');
  };

  const handleTestApiKey = async () => {
    await testApiKeyMutation.mutateAsync();
  };

  const handleUpdateNotifications = async (key: string, value: boolean) => {
    await updateNotificationsMutation.mutateAsync({ [key]: value });
  };

  const handleDeleteAccount = async () => {
    await deleteAccountMutation.mutateAsync();
  };

  if (profileLoading || notificationsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Logo spinning transparent className="w-8 h-8" />
      </div>
    );
  }

  const userInitials = profile?.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-semibold text-foreground mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your account and application preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Profile Settings */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="w-5 h-5 text-chart-2" />
                <CardTitle className="text-card-foreground">Profile Settings</CardTitle>
              </div>
              <p className="text-muted-foreground">Update your personal information</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4 mb-6">
                <Avatar className="w-16 h-16">
                  {profile?.avatar_url && <AvatarImage src={profile.avatar_url} />}
                  <AvatarFallback className="text-white text-xl bg-brand-orange">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <input
                    type="file"
                    id="avatar-upload"
                    className="hidden"
                    accept="image/jpeg,image/png"
                    onChange={handleAvatarUpload}
                    disabled={uploadAvatarMutation.isPending}
                  />
                  <Button
                    variant="outline"
                    className="border-border text-foreground"
                    onClick={() => document.getElementById('avatar-upload')?.click()}
                    disabled={uploadAvatarMutation.isPending}
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    {uploadAvatarMutation.isPending ? 'Uploading...' : 'Change Avatar'}
                  </Button>
                  <p className="text-xs text-muted-foreground mt-1">JPG or PNG, max 2MB</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    value={profileForm.full_name}
                    onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" value={profile?.email} disabled />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={profileForm.role}
                    onChange={(e) => setProfileForm({ ...profileForm, role: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="company">Company</Label>
                  <Input
                    id="company"
                    value={profileForm.company}
                    onChange={(e) => setProfileForm({ ...profileForm, company: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end">
                <Button
                  className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                  onClick={handleSaveProfile}
                  disabled={updateProfileMutation.isPending}
                >
                  {updateProfileMutation.isPending ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Appearance */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Palette className="w-5 h-5 text-chart-1" />
                <CardTitle className="text-card-foreground">Appearance</CardTitle>
              </div>
              <p className="text-muted-foreground">Customize the look and feel</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="theme-mode" className="text-card-foreground">Theme</Label>
                  <p className="text-sm text-muted-foreground">Choose between light and dark mode</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground capitalize">{theme}</span>
                  <ThemeToggle />
                </div>
              </div>

              <Separator className="bg-border" />

              <div className="grid grid-cols-2 gap-4">
                <Button
                  variant={theme === 'light' ? 'default' : 'outline'}
                  onClick={() => setTheme('light')}
                  className="justify-start h-auto p-4"
                >
                  <div className="flex flex-col items-start gap-2">
                    <div className="w-6 h-4 rounded border bg-white border-gray-300"></div>
                    <span>Light</span>
                  </div>
                </Button>

                <Button
                  variant={theme === 'dark' ? 'default' : 'outline'}
                  onClick={() => setTheme('dark')}
                  className="justify-start h-auto p-4"
                >
                  <div className="flex flex-col items-start gap-2">
                    <div className="w-6 h-4 rounded border bg-gray-800 border-gray-600"></div>
                    <span>Dark</span>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* API Configuration */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Key className="w-5 h-5 text-chart-5" />
                <CardTitle className="text-card-foreground">API Configuration</CardTitle>
              </div>
              <p className="text-muted-foreground">Manage your Google API key for persona generation</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg border border-amber-200 dark:border-amber-800">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="w-4 h-4 text-amber-600" />
                  <span className="text-sm font-medium text-amber-800 dark:text-amber-200">Important</span>
                </div>
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  Your API key is stored securely (encrypted) and only used for generating personas.
                </p>
              </div>

              <div>
                <Label htmlFor="api-key">Google API Key</Label>
                <div className="flex gap-2 mt-1">
                  <div className="relative flex-1">
                    <Input
                      id="api-key"
                      type={showApiKey ? "text" : "password"}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your Google API key"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3"
                      onClick={() => setShowApiKey(!showApiKey)}
                    >
                      {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </Button>
                  </div>
                  <Button
                    variant="outline"
                    onClick={handleTestApiKey}
                    disabled={testApiKeyMutation.isPending}
                  >
                    {testApiKeyMutation.isPending ? 'Testing...' : 'Test Connection'}
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Get your API key from{' '}
                  <a
                    href="https://makersuite.google.com/app/apikey"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-chart-1 hover:underline"
                  >
                    Google AI Studio
                  </a>
                </p>
              </div>

              <div className="flex justify-end">
                <Button
                  className="bg-brand-orange hover:bg-brand-orange/90 text-white"
                  onClick={handleSaveApiKey}
                  disabled={saveApiKeyMutation.isPending}
                >
                  {saveApiKeyMutation.isPending ? 'Saving...' : 'Save API Key'}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="w-5 h-5 text-chart-3" />
                <CardTitle className="text-card-foreground">Notifications</CardTitle>
              </div>
              <p className="text-muted-foreground">Choose what notifications you'd like to receive</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-card-foreground">Email Notifications</Label>
                    <p className="text-sm text-muted-foreground">Receive notifications via email</p>
                  </div>
                  <Switch
                    checked={notifications?.email_notifications_enabled}
                    onCheckedChange={(checked) =>
                      handleUpdateNotifications('email_notifications_enabled', checked)
                    }
                  />
                </div>

                <Separator className="bg-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-card-foreground">Discussion Complete</Label>
                    <p className="text-sm text-muted-foreground">Notify when focus groups finish</p>
                  </div>
                  <Switch
                    checked={notifications?.discussion_complete_notifications}
                    onCheckedChange={(checked) =>
                      handleUpdateNotifications('discussion_complete_notifications', checked)
                    }
                  />
                </div>

                <Separator className="bg-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-card-foreground">Weekly Reports</Label>
                    <p className="text-sm text-muted-foreground">Get weekly activity summaries</p>
                  </div>
                  <Switch
                    checked={notifications?.weekly_reports_enabled}
                    onCheckedChange={(checked) =>
                      handleUpdateNotifications('weekly_reports_enabled', checked)
                    }
                  />
                </div>

                <Separator className="bg-border" />

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-card-foreground">System Updates</Label>
                    <p className="text-sm text-muted-foreground">Important updates about new features</p>
                  </div>
                  <Switch
                    checked={notifications?.system_updates_notifications}
                    onCheckedChange={(checked) =>
                      handleUpdateNotifications('system_updates_notifications', checked)
                    }
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Account Status */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <CardTitle className="text-card-foreground">Account Status</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Plan</span>
                <Badge className={`capitalize ${
                  stats?.plan === 'enterprise'
                    ? 'bg-gradient-to-r from-chart-2/10 to-chart-5/10 text-chart-2 border-chart-2/20'
                    : 'bg-muted text-muted-foreground'
                }`}>
                  {stats?.plan}
                </Badge>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Projects</span>
                <span className="text-card-foreground">{stats?.projects_count || 0}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Personas Generated</span>
                <span className="text-card-foreground">{stats?.personas_count || 0}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Focus Groups</span>
                <span className="text-card-foreground">{stats?.focus_groups_count || 0}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">API Calls</span>
                <span className="text-card-foreground">
                  {stats?.api_calls_this_month || 0} / {stats?.api_calls_limit || 0}
                </span>
              </div>

              <Separator className="bg-border" />

              <Button variant="outline" className="w-full" disabled>
                Upgrade Plan (Coming Soon)
              </Button>
            </CardContent>
          </Card>

          {/* Data & Privacy */}
          <Card className="bg-card border border-border shadow-sm">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-chart-4" />
                <CardTitle className="text-card-foreground">Data & Privacy</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start" onClick={logout}>
                Logout
              </Button>

              <Button
                variant="outline"
                className="w-full justify-start border-destructive/50 text-destructive hover:bg-destructive/10"
                onClick={() => setShowDeleteDialog(true)}
              >
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Account Confirmation */}
      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title="Delete Account"
        description="Are you sure you want to delete your account? This action cannot be undone. All your projects, personas, and data will be permanently deleted after 30 days."
        confirmText="Delete My Account"
        confirmVariant="destructive"
        onConfirm={handleDeleteAccount}
      />
    </div>
  );
}
```

---

## 9. Integracja z Istniejącym Kodem

### 9.1 Update Projects API

Wszystkie endpointy w `app/api/projects.py` muszą zostać zmodyfikowane:

```python
from app.api.dependencies import get_current_user
from app.models.user import User

# Przykład: GET all projects
@router.get("/projects")
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Project).where(
            Project.owner_id == current_user.id,
            Project.deleted_at.is_(None)
        )
    )
    projects = result.scalars().all()
    return projects

# Przykład: POST create project
@router.post("/projects")
async def create_project(
    payload: CreateProjectPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_project = Project(
        **payload.dict(),
        owner_id=current_user.id  # ✅ Assign owner
    )
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project
```

**Powtórz dla WSZYSTKICH endpointów w:**
- `app/api/projects.py`
- `app/api/personas.py`
- `app/api/focus_groups.py`
- `app/api/surveys.py`
- `app/api/analysis.py`
- `app/api/graph_analysis.py`

### 9.2 Per-User API Keys

Gdy użytkownik ma własny API key, użyj go zamiast globalnego:

**Plik:** `app/services/persona_generator_langchain.py` (modyfikacja)

```python
from app.core.security import decrypt_api_key

class PersonaGeneratorLangChain:
    def __init__(self, user: Optional[User] = None):
        settings = get_settings()

        # Use user's API key if available, fallback to global
        api_key = settings.GOOGLE_API_KEY
        if user and user.encrypted_google_api_key:
            api_key = decrypt_api_key(user.encrypted_google_api_key)

        self.llm = ChatGoogleGenerativeAI(
            model=settings.PERSONA_GENERATION_MODEL,
            google_api_key=api_key,
            temperature=settings.TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )
```

**Powtórz w:**
- `FocusGroupServiceLangChain`
- `DiscussionSummarizerService`
- Wszystkich serwisach używających LLM

### 9.3 Sidebar Update

Dodaj user avatar i menu w sidebar:

**Plik:** `frontend/src/components/layout/AppSidebar.tsx` (modyfikacje)

```tsx
import { useAuth } from '@/contexts/AuthContext';
import { LogOut } from 'lucide-react';

export function AppSidebar({ currentView, onNavigate }: AppSidebarProps) {
  const { user, logout } = useAuth();

  return (
    <Sidebar className="...">
      {/* ... existing header ... */}

      <SidebarFooter className="p-4">
        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-sidebar-accent cursor-pointer">
          <Avatar className="w-8 h-8">
            {user?.avatar_url && <AvatarImage src={user.avatar_url} />}
            <AvatarFallback className="bg-brand-orange text-white text-xs">
              {user?.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground truncate">{user?.full_name}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
          <button
            onClick={logout}
            className="p-1 hover:bg-sidebar-accent-foreground/10 rounded"
            title="Logout"
          >
            <LogOut className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
```

---

## 10. Bezpieczeństwo

### 10.1 Security Checklist

**Backend:**
- ✅ Passwords hashed with bcrypt (min 10 rounds)
- ✅ JWT tokens signed with SECRET_KEY (min 32 chars)
- ✅ API keys encrypted with Fernet before storage
- ✅ Input validation on all endpoints (Pydantic)
- ✅ Email validation (EmailStr type)
- ✅ SQL injection protected (SQLAlchemy parametrization)
- ✅ CORS restricted to frontend origin
- ✅ Rate limiting (TODO: implement with slowapi)
- ✅ HTTPS enforced in production

**Frontend:**
- ✅ Tokens stored in localStorage (consider httpOnly cookies for production)
- ✅ Auto-logout on 401 responses
- ✅ Password visibility toggle
- ✅ File upload validation (type, size)
- ✅ XSS protection (React escapes by default)
- ✅ CSRF protection via JWT (stateless)

### 10.2 Production Recommendations

**Environment Variables (.env):**
```bash
# Generate strong SECRET_KEY
SECRET_KEY=$(openssl rand -hex 32)

# Use strong database passwords
POSTGRES_PASSWORD=$(openssl rand -base64 24)
NEO4J_PASSWORD=$(openssl rand -base64 24)

# Set environment
ENVIRONMENT=production
DEBUG=false

# HTTPS only
ALLOWED_ORIGINS=https://yourdomain.com
```

**Additional Security Measures:**
1. **Email Verification:** Implement email confirmation before account activation
2. **2FA (Optional):** Add TOTP-based two-factor authentication
3. **Rate Limiting:** Limit login attempts (5/minute per IP)
4. **Password Reset:** Implement forgot password flow
5. **Session Management:** Add token refresh mechanism
6. **Audit Logging:** Log all auth events (login, logout, failed attempts)
7. **Account Lockout:** Lock account after N failed login attempts

---

## 11. Kolejność Implementacji

### Faza 1: Backend Foundation (4-6h)
1. ✅ Utwórz model User (`app/models/user.py`)
2. ✅ Utwórz migrację Alembic
3. ✅ Uruchom migrację: `docker-compose exec api alembic upgrade head`
4. ✅ Implementuj security utils (`app/core/security.py`)
5. ✅ Implementuj dependencies (`app/api/dependencies.py`)
6. ✅ Implementuj auth endpoints (`app/api/auth.py`)
7. ✅ Testuj endpointy (Swagger UI)

### Faza 2: Settings Backend (2-3h)
1. ✅ Implementuj settings endpoints (`app/api/settings.py`)
2. ✅ Dodaj static files mounting do main.py
3. ✅ Utwórz folder `static/avatars/`
4. ✅ Testuj wszystkie endpointy

### Faza 3: Update Existing Endpoints (2-3h)
1. ✅ Dodaj `get_current_user` dependency do wszystkich endpoints
2. ✅ Aktualizuj queries (filtruj po `owner_id`)
3. ✅ Aktualizuj serwisy (per-user API keys)
4. ✅ Testuj każdy endpoint

### Faza 4: Frontend Auth (3-4h)
1. ✅ Utwórz AppLoader component
2. ✅ Utwórz Auth API client
3. ✅ Implementuj AuthContext
4. ✅ Utwórz Login component
5. ✅ Zaktualizuj App.tsx (routing logic)
6. ✅ Zaktualizuj main.tsx (AuthProvider)
7. ✅ Testuj flow: register → login → logout

### Faza 5: Frontend Settings (3-4h)
1. ✅ Utwórz Settings API client
2. ✅ Implementuj useSettings hooks
3. ✅ Refaktoruj Settings.tsx (podłącz do API)
4. ✅ Implementuj upload avatara
5. ✅ Implementuj delete account
6. ✅ Testuj wszystkie features

### Faza 6: Integration & Polish (2-3h)
1. ✅ Zaktualizuj AppSidebar (user avatar + logout)
2. ✅ Testuj E2E flow
3. ✅ Dodaj loading states
4. ✅ Dodaj error handling
5. ✅ Responsive design check
6. ✅ Dark mode check

### Faza 7: Testing & Documentation (2-3h)
1. ✅ Manual testing wszystkich features
2. ✅ Fix bugs
3. ✅ Aktualizuj CLAUDE.md
4. ✅ Dodaj README sekcję o auth
5. ✅ Commit i push

**Łączny czas:** 18-26 godzin roboczych (2-3 dni full-time)

---

## 12. Struktura Plików

### Backend (Nowe pliki)
```
app/
├── models/
│   └── user.py                     # User model (NOWY)
├── api/
│   ├── auth.py                     # Auth endpoints (NOWY)
│   ├── settings.py                 # Settings endpoints (NOWY)
│   └── dependencies.py             # Auth guards (NOWY)
├── core/
│   └── security.py                 # Hashing, JWT, encryption (NOWY)
└── db/
    └── session.py                  # DB session (sprawdź czy istnieje)

alembic/
└── versions/
    └── XXXX_create_users_table.py  # Migration (NOWY)

static/
└── avatars/                        # User avatars (NOWY FOLDER)
```

### Frontend (Nowe pliki)
```
frontend/src/
├── components/
│   ├── AppLoader.tsx               # Loading screen (NOWY)
│   └── auth/
│       └── Login.tsx               # Login/Register screen (NOWY)
├── contexts/
│   └── AuthContext.tsx             # Auth state management (NOWY)
├── hooks/
│   └── useSettings.ts              # Settings React Query hooks (NOWY)
└── lib/
    └── api.ts                      # Rozszerzenie o auth & settings API
```

### Zmodyfikowane pliki
```
Backend:
- app/main.py                       # Dodaj routery, static files
- app/models/project.py             # Dodaj owner_id
- app/api/projects.py               # Dodaj auth dependency
- app/api/personas.py               # Dodaj auth dependency
- app/api/focus_groups.py           # Dodaj auth dependency
- app/api/surveys.py                # Dodaj auth dependency
- app/api/analysis.py               # Dodaj auth dependency
- app/api/graph_analysis.py         # Dodaj auth dependency
- app/services/*.py                 # Per-user API keys

Frontend:
- frontend/src/App.tsx              # Routing logic
- frontend/src/main.tsx             # AuthProvider wrapper
- frontend/src/components/Settings.tsx  # Pełna refaktoryzacja
- frontend/src/components/layout/AppSidebar.tsx  # User menu
```

---

## 13. Testing Checklist

### Backend API Testing (via Swagger)
- [ ] POST `/api/v1/auth/register` - utwórz konto
- [ ] POST `/api/v1/auth/login` - zaloguj się
- [ ] GET `/api/v1/auth/me` - pobierz dane użytkownika
- [ ] GET `/api/v1/settings/profile` - pobierz profil
- [ ] PUT `/api/v1/settings/profile` - zaktualizuj profil
- [ ] POST `/api/v1/settings/avatar` - upload avatar
- [ ] PUT `/api/v1/settings/api-key` - zapisz API key
- [ ] POST `/api/v1/settings/api-key/test` - testuj API key
- [ ] GET `/api/v1/settings/notifications` - pobierz notyfikacje
- [ ] PUT `/api/v1/settings/notifications` - zaktualizuj notyfikacje
- [ ] GET `/api/v1/settings/stats` - pobierz statystyki
- [ ] DELETE `/api/v1/settings/account` - usuń konto

### Frontend E2E Testing
- [ ] Otwórz app → pokazuje loading screen
- [ ] Loading → przekierowanie na login
- [ ] Rejestracja nowego konta
- [ ] Logout → przekierowanie na login
- [ ] Login z błędnym hasłem → error message
- [ ] Login z poprawnymi danymi → dashboard
- [ ] Nawigacja do Settings
- [ ] Edycja profilu → success toast
- [ ] Upload avatara → zmiana widoczna
- [ ] Zmiana theme → dark/light działa
- [ ] Zapisz API key → success toast
- [ ] Test API key → pokazuje result
- [ ] Zmiana notyfikacji → zapisuje się
- [ ] Sprawdź statystyki → wyświetla liczby
- [ ] Delete account → confirm dialog → logout

### Integration Testing
- [ ] Utwórz projekt → owner_id ustawiony
- [ ] Wygeneruj persony → używa user API key (jeśli ustawiony)
- [ ] Uruchom focus group → działa z user context
- [ ] Drugi user nie widzi projektów pierwszego
- [ ] Token expiry → auto-logout
- [ ] Refresh page → pozostaje zalogowany

---

## 14. Troubleshooting

### Błędy podczas migracji
```bash
# Reset database (UWAGA: usuwa wszystkie dane!)
docker-compose down -v
docker-compose up -d
docker-compose exec api alembic upgrade head

# Albo rollback i ponowne upgrade
docker-compose exec api alembic downgrade -1
docker-compose exec api alembic upgrade head
```

### CORS errors
Sprawdź `ALLOWED_ORIGINS` w `.env`:
```bash
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### JWT errors (401 Unauthorized)
1. Sprawdź czy token jest w localStorage
2. Sprawdź czy `SECRET_KEY` jest taki sam (backend)
3. Sprawdź czy token nie wygasł (30 min TTL)

### API key encryption errors
Upewnij się że `SECRET_KEY` ma przynajmniej 32 znaki:
```python
# W .env
SECRET_KEY=$(openssl rand -hex 32)
```

### Avatar upload nie działa
1. Sprawdź czy folder `static/avatars/` istnieje
2. Sprawdź uprawnienia: `chmod 755 static/avatars`
3. Sprawdź czy FastAPI mountuje static files

---

## 15. Dodatkowe Usprawnienia (Future Enhancements)

### Faza 2 (po MVP)
1. **Email Verification:** Wyślij link potwierdzający po rejestracji
2. **Password Reset:** Forgot password flow
3. **Social Login:** Google OAuth, GitHub OAuth
4. **Team Accounts:** Multi-user projects (collaboration)
5. **API Usage Tracking:** Redis counter per user
6. **Storage Tracking:** Calculate total data size per user
7. **Plan Limits:** Enforce API call limits
8. **Billing Integration:** Stripe dla płatnych planów
9. **Audit Logs:** Historia działań użytkownika
10. **Notifications System:** Real-time powiadomienia (WebSocket)

### Faza 3 (advanced)
1. **2FA/MFA:** TOTP via Google Authenticator
2. **SSO:** SAML dla enterprise clients
3. **Role-Based Access Control (RBAC):** Admin, Editor, Viewer roles
4. **Data Export:** JSON export wszystkich danych użytkownika
5. **GDPR Compliance:** Data deletion, consent management
6. **Rate Limiting:** Per-user API throttling
7. **Account Recovery:** Backup codes, account unlock
8. **Session Management:** Multiple devices, logout all sessions

---

## 16. Podsumowanie

### Co zostanie zaimplementowane:
✅ **Loading Screen** - Animowany interfejs podczas inicjalizacji
✅ **System Logowania** - Rejestracja, login, JWT auth
✅ **Protected API** - Wszystkie endpointy wymagają autentykacji
✅ **Panel Settings** - Funkcjonalny, połączony z backend:
  - Edycja profilu (nazwa, firma, rola)
  - Upload avatara
  - Zarządzanie Google API key (szyfrowane)
  - Test połączenia API
  - Ustawienia notyfikacji
  - Statystyki konta
  - Usuwanie konta
✅ **Dark/Light Theme** - Już działa, pozostaje bez zmian
✅ **User-specific Data** - Każdy user widzi tylko swoje projekty
✅ **Per-User API Keys** - Możliwość używania własnego klucza Gemini

### Bezpieczeństwo:
✅ Bcrypt password hashing
✅ JWT token authentication
✅ Fernet API key encryption
✅ Input validation (Pydantic)
✅ SQL injection protection (SQLAlchemy)
✅ CORS configuration
✅ Soft delete (30-day retention)

### Szacowany czas: 18-26 godzin
- Backend: 8-12h
- Frontend: 6-10h
- Integration: 2-3h
- Testing: 2-3h

### Plik gotowy do implementacji!

---

**Koniec planu implementacji**
**Następny krok:** Rozpocznij od Fazy 1 (Backend Foundation)
