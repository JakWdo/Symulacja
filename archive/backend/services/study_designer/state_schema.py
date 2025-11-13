"""
State Schema dla Study Designer Chat (LangGraph)

Definuje strukturę stanu konwersacji przechowywannego w LangGraph.
Stan jest persystowany do PostgreSQL (JSON column) między wiadomościami.

Główne pola:
- session_id: UUID sesji
- messages: Historia konwersacji (user/assistant)
- current_stage: Obecny etap (welcome, gather_goal, etc.)
- Zebrane dane: study_goal, target_audience, research_method, konfiguracja
- generated_plan: Wygenerowany plan badania
"""

from __future__ import annotations

from typing import TypedDict, Literal, NotRequired
from datetime import datetime


class ConversationState(TypedDict):
    """
    Stan konwersacji Study Designer (LangGraph state).

    Ten TypedDict definiuje pełny stan konwersacji między użytkownikiem a AI.
    Stan jest aktualizowany przez każdy node i persystowany do DB.

    Attributes:
        # === SESSION INFO ===
        session_id: UUID sesji (string)
        user_id: UUID użytkownika
        project_id: UUID projektu (może być None)

        # === CONVERSATION HISTORY ===
        messages: Lista wiadomości [{"role": "user|assistant", "content": "..."}]
        current_stage: Aktualny etap konwersacji (node name)
        last_activity: ISO timestamp ostatniej aktywności

        # === GATHERED INFORMATION ===
        study_goal: Cel badania (zbierany w gather_goal node)
        study_goal_confirmed: Czy cel został potwierdzony przez użytkownika

        target_audience: Grupa docelowa (zbierana w define_audience node)
            {
                "age_range": {"min": 25, "max": 35},
                "gender_distribution": {"female": 60, "male": 40},
                "locations": ["Warszawa", "Kraków", "Wrocław"],
                "characteristics": ["początkujący", "średniozaawansowani"],
                "user_type": "obecni użytkownicy darmowej wersji"
            }

        research_method: Wybrana metoda badawcza (select_method node)
            "personas" | "focus_group" | "survey" | "mixed"

        num_personas: Liczba person do wygenerowania

        focus_group_config: Konfiguracja grupy fokusowej (configure_details node)
            {
                "num_questions": 4,
                "questions": ["Q1", "Q2", "Q3", "Q4"],
                "discussion_format": "async",
                "target_insights": ["wartość", "cena", "porównanie"]
            }

        survey_config: Konfiguracja ankiety (configure_details node)
            {
                "num_questions": 10,
                "question_types": ["single_choice", "multi_choice", "open"],
                "topics": [...]
            }

        # === GENERATED PLAN ===
        generated_plan: Plan badania (generate_plan node)
            {
                "name": str,
                "description": str,
                "markdown_summary": str,  # Ładny markdown do wyświetlenia
                "workflow_data": {...},  # WorkflowCreate compatible
                "estimated_time_seconds": int,
                "estimated_cost_usd": float,
                "deliverables": [...]
            }

        plan_approved: Czy plan został zatwierdzony

        # === METADATA ===
        created_at: ISO timestamp utworzenia sesji
        completed_at: ISO timestamp zakończenia (nullable)

        # === LLM TRACKING ===
        total_tokens_used: Suma tokenów użytych w całej konwersacji
        total_cost_usd: Suma kosztów LLM
    """

    # === SESSION INFO ===
    session_id: str
    user_id: str
    project_id: NotRequired[str | None]

    # === CONVERSATION HISTORY ===
    messages: list[dict[str, str]]  # [{"role": "user", "content": "..."}]
    current_stage: Literal[
        "welcome",
        "gather_goal",
        "define_audience",
        "select_method",
        "configure_details",
        "generate_plan",
        "await_approval",
        "execute",
    ]
    last_activity: str  # ISO format datetime

    # === GATHERED INFORMATION ===
    study_goal: NotRequired[str | None]
    study_goal_confirmed: NotRequired[bool]

    target_audience: NotRequired[dict | None]  # Structured demographics

    research_method: NotRequired[
        Literal["personas", "focus_group", "survey", "mixed"] | None
    ]

    num_personas: NotRequired[int | None]

    focus_group_config: NotRequired[dict | None]

    survey_config: NotRequired[dict | None]

    # === GENERATED PLAN ===
    generated_plan: NotRequired[dict | None]
    plan_approved: NotRequired[bool]

    # === METADATA ===
    created_at: str  # ISO format datetime
    completed_at: NotRequired[str | None]

    # === LLM TRACKING ===
    total_tokens_used: NotRequired[int]
    total_cost_usd: NotRequired[float]


def create_initial_state(
    session_id: str,
    user_id: str,
    project_id: str | None = None,
) -> ConversationState:
    """
    Tworzy początkowy stan konwersacji.

    Args:
        session_id: UUID sesji
        user_id: UUID użytkownika
        project_id: UUID projektu (opcjonalnie)

    Returns:
        ConversationState: Początkowy stan z pustymi polami
    """
    now = datetime.utcnow().isoformat()

    return ConversationState(
        session_id=session_id,
        user_id=user_id,
        project_id=project_id,
        messages=[],
        current_stage="welcome",
        last_activity=now,
        created_at=now,
        total_tokens_used=0,
        total_cost_usd=0.0,
        study_goal=None,
        study_goal_confirmed=False,
        target_audience=None,
        research_method=None,
        num_personas=None,
        focus_group_config=None,
        survey_config=None,
        generated_plan=None,
        plan_approved=False,
        completed_at=None,
    )


def serialize_state(state: ConversationState) -> dict:
    """
    Serializuje stan do JSON (do zapisu w PostgreSQL).

    Args:
        state: ConversationState object

    Returns:
        dict: JSON-serializable dict
    """
    # TypedDict is already dict-compatible, but we ensure types
    return dict(state)


def deserialize_state(data: dict) -> ConversationState:
    """
    Deserializuje stan z JSON (z PostgreSQL).

    Args:
        data: JSON dict z bazy danych

    Returns:
        ConversationState: Typed state object

    Raises:
        KeyError: Jeśli brakuje wymaganych pól
    """
    # Ensure required fields exist
    required_fields = [
        "session_id",
        "user_id",
        "messages",
        "current_stage",
        "last_activity",
        "created_at",
    ]

    for field in required_fields:
        if field not in data:
            raise KeyError(f"Missing required field in conversation state: {field}")

    return ConversationState(**data)  # type: ignore


def update_last_activity(state: ConversationState) -> None:
    """
    Aktualizuje timestamp ostatniej aktywności (in-place).

    Args:
        state: ConversationState do aktualizacji
    """
    state["last_activity"] = datetime.utcnow().isoformat()


def add_message(
    state: ConversationState,
    role: Literal["user", "assistant", "system"],
    content: str,
) -> None:
    """
    Dodaje wiadomość do historii konwersacji (in-place).

    Args:
        state: ConversationState do aktualizacji
        role: Rola nadawcy (user/assistant/system)
        content: Treść wiadomości
    """
    state["messages"].append({"role": role, "content": content})
    update_last_activity(state)


def get_last_user_message(state: ConversationState) -> str | None:
    """
    Pobiera ostatnią wiadomość użytkownika.

    Args:
        state: ConversationState

    Returns:
        str | None: Treść ostatniej wiadomości użytkownika lub None
    """
    for msg in reversed(state["messages"]):
        if msg["role"] == "user":
            return msg["content"]
    return None
