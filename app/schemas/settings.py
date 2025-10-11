"""
Schemas dla ustawień użytkownika i zarządzania kontem

Pydantic schemas używane przez endpointy /settings/*
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional


# === PROFILE SCHEMAS ===
class ProfileUpdateRequest(BaseModel):
    """Request do aktualizacji profilu użytkownika"""
    full_name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None

    @validator('full_name')
    def validate_name(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return v.strip() if v else v


class ProfileResponse(BaseModel):
    """Szczegółowy profil użytkownika"""
    id: str
    email: str
    full_name: str
    role: Optional[str]
    company: Optional[str]
    avatar_url: Optional[str]
    plan: str
    is_verified: bool
    created_at: str
    last_login_at: Optional[str]

    class Config:
        from_attributes = True


# === NOTIFICATION SCHEMAS ===
class NotificationSettingsResponse(BaseModel):
    """Ustawienia notyfikacji użytkownika"""
    email_notifications_enabled: bool
    discussion_complete_notifications: bool
    weekly_reports_enabled: bool
    system_updates_notifications: bool

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    """Request do aktualizacji ustawień notyfikacji"""
    email_notifications_enabled: Optional[bool] = None
    discussion_complete_notifications: Optional[bool] = None
    weekly_reports_enabled: Optional[bool] = None
    system_updates_notifications: Optional[bool] = None


# === ACCOUNT STATS SCHEMAS ===
class AccountStatsResponse(BaseModel):
    """Statystyki konta użytkownika"""
    plan: str
    projects_count: int
    personas_count: int
    focus_groups_count: int
    surveys_count: int


# === API KEY SCHEMAS ===
class ApiKeyUpdateRequest(BaseModel):
    """Request do aktualizacji Google API key"""
    api_key: str

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('API key must be at least 10 characters')
        # Google API keys typically start with "AIza"
        if not v.startswith('AIza'):
            raise ValueError('Invalid Google API key format (should start with "AIza")')
        return v.strip()


class ApiKeyTestResponse(BaseModel):
    """Odpowiedź z testu połączenia API"""
    success: bool
    message: str
    model_tested: Optional[str] = None
    error: Optional[str] = None


# === AVATAR SCHEMAS ===
class AvatarUploadResponse(BaseModel):
    """Odpowiedź po uploadzie avatara"""
    message: str
    avatar_url: str


# === GENERAL RESPONSES ===
class MessageResponse(BaseModel):
    """Ogólna odpowiedź z wiadomością"""
    message: str
    user: Optional[ProfileResponse] = None
