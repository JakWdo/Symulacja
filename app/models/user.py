"""
Model użytkownika z pełnym wsparciem dla autentykacji i ustawień

Ten model reprezentuje użytkownika systemu Market Research SaaS.
Zawiera dane profilowe, ustawienia notyfikacji, szyfrowany API key i relacje do projektów.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text
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
    avatar_url = Column(String(500), nullable=True)  # URL do avatara

    # === API CONFIGURATION ===
    # Szyfrowany Google API key (używany zamiast globalnego settings.GOOGLE_API_KEY)
    encrypted_google_api_key = Column(Text, nullable=True)

    # === NOTIFICATION SETTINGS ===
    email_notifications_enabled = Column(Boolean, default=True)
    discussion_complete_notifications = Column(Boolean, default=True)
    weekly_reports_enabled = Column(Boolean, default=False)
    system_updates_notifications = Column(Boolean, default=True)

    # === ACCOUNT STATUS ===
    is_active = Column(Boolean, default=True)  # Account enabled/disabled
    is_verified = Column(Boolean, default=False)  # Email verified (future feature)
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
