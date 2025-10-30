"""
Model użytkownika z pełnym wsparciem dla autentykacji i ustawień

Ten model reprezentuje użytkownika systemu Sight.
Zawiera dane profilowe, ustawienia notyfikacji, szyfrowany API key i relacje do projektów.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.db.base import Base


class User(Base):
    """
    Użytkownik systemu z autentykacją i ustawieniami

    Relacje:
    - projects: Lista projektów należących do użytkownika (1:N)
    - personas: Wszystkie persony utworzone przez użytkownika (poprzez projekty)

    Bezpieczeństwo:
    - Hasło przechowywane jako bcrypt hash
    - API key szyfrowany przez Fernet przed zapisem
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
    avatar_url = Column(String(500), nullable=True)  # Adres URL do avatara

    # === API CONFIGURATION ===
    # Szyfrowany Google API key (używany zamiast globalnego settings.GOOGLE_API_KEY)
    encrypted_google_api_key = Column(Text, nullable=True)

    # === NOTIFICATION SETTINGS ===
    email_notifications_enabled = Column(Boolean, default=True)
    discussion_complete_notifications = Column(Boolean, default=True)
    weekly_reports_enabled = Column(Boolean, default=False)
    system_updates_notifications = Column(Boolean, default=True)

    # === ACCOUNT STATUS ===
    is_active = Column(Boolean, default=True)  # Czy konto jest aktywne
    is_verified = Column(Boolean, default=False)  # Czy adres e-mail został zweryfikowany (funkcja przyszłościowa)
    plan = Column(String(50), default="free")  # Plany taryfowe: "free", "pro", "enterprise"

    # === BUDGET SETTINGS ===
    budget_limit = Column(Float, nullable=True)  # Custom budget limit (USD), overrides plan-based limit
    warning_threshold = Column(Integer, default=80)  # Warning alert threshold (% of budget)
    critical_threshold = Column(Integer, default=90)  # Critical alert threshold (% of budget)

    # === TIMESTAMPS ===
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Miękkie usunięcie (data dezaktywacji)

    # === RELATIONSHIPS ===
    projects = relationship(
        "Project",
        foreign_keys="Project.owner_id",  # Explicit FK: tylko owner_id, NIE deleted_by
        back_populates="owner",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"
