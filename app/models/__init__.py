"""
Modele ORM SQLAlchemy - Warstwa Danych

Zawiera wszystkie modele bazodanowe aplikacji (PostgreSQL):

- User: Użytkownicy systemu (autentykacja i ustawienia)
- Project: Projekty badawcze (kontenery dla person i badań)
- Persona: Syntetyczne persony z demografią + psychologią (Big Five, Hofstede)
- FocusGroup: Grupy fokusowe - dyskusje między personami
- PersonaEvent: Event sourcing - historia działań każdej persony (z embeddingami)
- PersonaResponse: Odpowiedzi person na pytania w grupach fokusowych
- Survey: Ankiety syntetyczne (pytania + konfiguracja)
- SurveyResponse: Odpowiedzi person na ankiety
- RAGDocument: Dokumenty RAG - baza wiedzy (PDF/DOCX) dla generowania person

Wszystkie modele używają:
- UUID jako primary key
- Soft delete (deleted_at lub is_active)
- Timestamps (created_at, updated_at)
- Async SQLAlchemy relationships
"""

from .user import User
from .project import Project
from .persona import Persona
from .persona_audit import PersonaAuditLog
from .focus_group import FocusGroup
from .persona_events import PersonaEvent, PersonaResponse
from .survey import Survey, SurveyResponse
from .rag_document import RAGDocument

__all__ = [
    "User",
    "Project",
    "Persona",
    "PersonaAuditLog",
    "FocusGroup",
    "PersonaEvent",
    "PersonaResponse",
    "Survey",
    "SurveyResponse",
    "RAGDocument",
]
