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
- Workflow: Wieloetapowe przepływy badawcze (Workflow Builder)
- WorkflowStep: Pojedyncze kroki w workflow (nodes z React Flow)
- WorkflowExecution: Historia wykonań workflow z tracking statusu
- StudyDesignerSession: Sesje interaktywnego projektowania badań przez chat
- StudyDesignerMessage: Wiadomości w konwersacji Study Designer

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
from .workflow import (
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    WorkflowStatusEnum,
    ExecutionStatusEnum,
    WorkflowStepTypeEnum,
)
from .dashboard import (
    DashboardMetric,
    ProjectHealthLog,
    InsightEvidence,
    UsageMetric,
    UserNotification,
    ActionLog,
)
from .generation_progress import GenerationProgress, GenerationStage
from .study_designer import (
    StudyDesignerSession,
    StudyDesignerMessage,
    SessionStatusEnum,
    MessageRoleEnum,
    ConversationStageEnum,
)

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
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "WorkflowStatusEnum",
    "ExecutionStatusEnum",
    "WorkflowStepTypeEnum",
    "DashboardMetric",
    "ProjectHealthLog",
    "InsightEvidence",
    "UsageMetric",
    "UserNotification",
    "ActionLog",
    "GenerationProgress",
    "GenerationStage",
    "StudyDesignerSession",
    "StudyDesignerMessage",
    "SessionStatusEnum",
    "MessageRoleEnum",
    "ConversationStageEnum",
]
