"""
Schematy Pydantic dla Node Configs - 14 typów węzłów workflow

Zawiera:
1. Start/End nodes - StartNodeConfig, EndNodeConfig
2. Core action nodes - CreateProjectNodeConfig, GeneratePersonasNodeConfig, CreateSurveyNodeConfig, RunFocusGroupNodeConfig, AnalyzeResultsNodeConfig
3. Control flow nodes - DecisionNodeConfig, WaitNodeConfig
4. Integration nodes - ExportPDFNodeConfig, WebhookNodeConfig
5. Advanced logic nodes - ConditionNodeConfig, LoopNodeConfig, MergeNodeConfig
6. NodeConfig union type

Konwencje:
- Polish docstrings
- Field() z description dla każdego pola
- Validators gdzie potrzebne (condition, ai_prompt, url)
- MVP status markers (⚠️ OUT OF SCOPE MVP) dla disabled features
- Min/max constraints dla string lengths i int ranges
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator, ValidationInfo


# ==================== NODE CONFIG SCHEMAS (14 TYPES) ====================


class StartNodeConfig(BaseModel):
    """
    Konfiguracja węzła Start (trigger point).

    Start node jest entry point workflow - automatyczny trigger przy wykonaniu.

    MVP: Tylko manual trigger (user kliknie "Run Workflow").
    Future: scheduled (cron), webhook, event-based triggers.

    Validation rules:
    - Każdy workflow musi mieć dokładnie 1 Start node
    - Start node nie może mieć incoming edges
    """

    trigger_type: Literal["manual"] = Field(
        default="manual",
        description="Typ wyzwalacza (MVP: tylko manual)"
    )


class EndNodeConfig(BaseModel):
    """
    Konfiguracja węzła End (completion).

    End node kończy wykonanie workflow.
    Może mieć custom success message wyświetlany użytkownikowi.

    Validation rules:
    - Każdy workflow musi mieć ≥1 End node
    - End node nie może mieć outgoing edges
    - Wszystkie workflow paths muszą prowadzić do End node
    """

    success_message: str | None = Field(
        None,
        max_length=500,
        description="Komunikat po zakończeniu workflow"
    )


class CreateProjectNodeConfig(BaseModel):
    """
    Konfiguracja węzła Create Project.

    Tworzy nowy projekt badawczy jako kontener dla person, surveys, focus groups.

    Pola:
    - project_name: Nazwa projektu (wymagane)
    - project_description: Opis projektu (opcjonalne)
    - target_demographics: Docelowa demografia (opcjonalne, używa defaults jeśli None)

    Przykład target_demographics:
    {
      "age": {"min": 18, "max": 65},
      "gender": {"male": 50, "female": 45, "non-binary": 5},
      "locations": ["Warszawa", "Kraków", "Wrocław"]
    }
    """

    project_name: str = Field(..., min_length=1, max_length=255)
    project_description: str | None = Field(None, max_length=2000)
    target_demographics: dict | None = Field(
        None,
        description="Docelowa demografika {age: {min: 18, max: 65}, gender: {...}}"
    )


class GeneratePersonasNodeConfig(BaseModel):
    """
    Konfiguracja węzła Generate Personas.

    Generuje AI personas używając PersonaOrchestrationService.

    Pola podstawowe:
    - count: Liczba person do wygenerowania (5-100, Pro: 50, Enterprise: unlimited)
    - demographic_preset: Preset demograficzny (gen_z, millennials, gen_x, etc.)
    - target_audience_description: Opis grupy docelowej

    Advanced options:
    - advanced_options: Zaawansowane opcje targetowania (PersonaGenerationAdvancedOptions)
      Może zawierać: age_focus, gender_balance, urbanicity, industries, etc.

    Estimated time: 30-45s dla 20 person

    Przykład:
    {
      "count": 20,
      "demographic_preset": "millennials",
      "target_audience_description": "Tech-savvy professionals from Warsaw",
      "advanced_options": {
        "urbanicity": "urban",
        "industries": ["tech", "finance"]
      }
    }
    """

    count: int = Field(..., ge=1, le=100, description="Liczba person do wygenerowania")
    demographic_preset: str | None = Field(
        None,
        description="Preset demograficzny (gen_z, millennials, gen_x, etc.)"
    )
    target_audience_description: str | None = Field(
        None,
        max_length=500,
        description="Opis grupy docelowej"
    )
    advanced_options: dict | None = Field(
        None,
        description="Zaawansowane opcje targetowania (PersonaGenerationAdvancedOptions)"
    )


class CreateSurveyNodeConfig(BaseModel):
    """
    Konfiguracja węzła Create Survey.

    Tworzy ankietę z manual config lub AI-generated questions.

    Tryby:
    1. Manual questions: Podaj listę pytań w questions
    2. AI-generated: Ustaw ai_generate_questions=true i podaj ai_prompt
    3. Template: Użyj template_id (nps, satisfaction, etc.)

    Question types:
    - text-long: Otwarte pytanie tekstowe
    - text-short: Krótka odpowiedź
    - multiple-choice-single: Wybór jednej opcji
    - multiple-choice-multi: Wybór wielu opcji
    - rating-scale: Skala 1-5 lub 1-10
    - likert: Skala Likerta (strongly disagree - strongly agree)

    Przykład question:
    {
      "type": "multiple-choice-single",
      "text": "Which feature is most important?",
      "options": ["Push notifications", "Dark mode", "Offline mode"],
      "required": true
    }
    """

    survey_title: str = Field(..., min_length=1, max_length=255)
    survey_description: str | None = Field(None, max_length=2000)
    template_id: str | None = Field(
        None,
        description="ID szablonu ankiety (nps, satisfaction, etc.) - optional"
    )
    questions: list[dict] | None = Field(
        None,
        description="Lista pytań {type: 'text'|'rating'|'choice', text: '...', options: [...]}"
    )
    ai_generate_questions: bool = Field(
        default=False,
        description="Czy generować pytania AI (jeśli True, questions ignorowane)"
    )
    ai_prompt: str | None = Field(
        None,
        max_length=1000,
        description="Prompt dla AI do generacji pytań (tylko gdy ai_generate_questions=True)"
    )

    @field_validator('ai_prompt')
    @classmethod
    def validate_ai_prompt(cls, v: str | None, info: ValidationInfo) -> str | None:
        """
        Waliduj że ai_prompt jest podany gdy ai_generate_questions=True.

        Args:
            v: Wartość ai_prompt
            info: Kontekst walidacji z dostępem do innych pól

        Returns:
            Zwalidowany ai_prompt

        Raises:
            ValueError: Jeśli ai_generate_questions=True ale brak ai_prompt
        """
        if info.data.get('ai_generate_questions') and not v:
            raise ValueError("ai_prompt is required when ai_generate_questions=True")
        return v


class RunFocusGroupNodeConfig(BaseModel):
    """
    Konfiguracja węzła Run Focus Group.

    Przeprowadza symulowaną grupę fokusową z AI personas.

    Pola:
    - focus_group_title: Tytuł dyskusji
    - topics: Lista tematów do dyskusji (1-10 items)
    - participant_ids: Lista UUID person (jeśli None - użyj z poprzedniego node)
    - moderator_style: Styl moderatora (neutral/probing/directive)
    - rounds: Liczba rund dyskusji (1-5)

    Estimated time: 90-120s (zależy od liczby personas i topics)

    Przykład:
    {
      "focus_group_title": "Mobile App Features Discussion",
      "topics": [
        "What features do you use most?",
        "What frustrations do you experience?"
      ],
      "participant_ids": null,
      "moderator_style": "neutral",
      "rounds": 3
    }
    """

    focus_group_title: str = Field(..., min_length=1, max_length=255)
    topics: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Lista tematów do dyskusji"
    )
    participant_ids: list[UUID] | None = Field(
        None,
        description="Lista UUID person (jeśli None - użyj output z poprzedniego node)"
    )
    moderator_style: Literal["neutral", "probing", "directive"] = Field(
        default="neutral",
        description="Styl moderatora"
    )
    rounds: int = Field(default=3, ge=1, le=5, description="Liczba rund dyskusji")


class AnalyzeResultsNodeConfig(BaseModel):
    """
    Konfiguracja węzła Analyze Results.

    AI analysis wszystkich rezultatów z poprzednich nodes.

    Analysis types:
    - summary: Ogólne podsumowanie
    - sentiment: Analiza sentymentu (positive/neutral/negative breakdown)
    - themes: Ekstrakcja głównych tematów
    - insights: Głębokie insights i rekomendacje

    Input sources:
    - focus_group: Dane z focus group messages
    - survey: Dane z survey responses
    - personas: Analiza profili person

    Przykład:
    {
      "analysis_type": "summary",
      "input_source": "focus_group",
      "prompt_template": null
    }
    """

    analysis_type: Literal["summary", "sentiment", "themes", "insights"] = Field(
        default="summary",
        description="Typ analizy"
    )
    input_source: Literal["focus_group", "survey", "personas"] = Field(
        ...,
        description="Skąd brać dane do analizy"
    )
    prompt_template: str | None = Field(
        None,
        max_length=2000,
        description="Custom prompt dla LLM (optional)"
    )


class DecisionNodeConfig(BaseModel):
    """
    Konfiguracja węzła Decision (conditional branching).

    Decision node ewaluuje condition i wybiera branch (true/false).

    Condition: Python expression (bezpieczny subset):
    - Dozwolone: operatory porównania (==, !=, <, >, <=, >=), logiczne (and, or, not)
    - Zabronione: import, exec, eval, __import__, open, file

    Przykłady condition:
    - "len(personas) > 10"
    - "survey_nps_score >= 7"
    - "sentiment['positive'] > 60"

    Validation rules:
    - Decision node musi mieć dokładnie 2 outgoing edges (true branch, false branch)

    Przykład:
    {
      "condition": "survey_nps_score >= 7",
      "true_branch_label": "Positive feedback",
      "false_branch_label": "Needs improvement"
    }
    """

    condition: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Warunek do ewaluacji (Python expression)"
    )
    true_branch_label: str = Field(default="Yes", max_length=50)
    false_branch_label: str = Field(default="No", max_length=50)

    @field_validator('condition')
    @classmethod
    def validate_condition(cls, v: str) -> str:
        """
        Podstawowa walidacja składni condition.

        Sprawdza czy condition nie zawiera zabronionych słów kluczowych.

        Args:
            v: Wartość condition

        Returns:
            Zwalidowany condition

        Raises:
            ValueError: Jeśli condition zawiera zabronione keywords
        """
        forbidden = ['import', 'exec', 'eval', '__import__', 'open', 'file']
        if any(word in v.lower() for word in forbidden):
            raise ValueError(f"Forbidden keywords in condition: {forbidden}")
        return v


class WaitNodeConfig(BaseModel):
    """
    Konfiguracja węzła Wait (delay execution).

    ⚠️ OUT OF SCOPE MVP - DISABLED

    Wait node opóźnia wykonanie workflow o określony czas.
    Użyteczny dla scheduled workflows w przyszłości.

    Validation: Raise NotImplementedError w executor

    Przykład (future):
    {
      "duration_seconds": 3600
    }
    """

    duration_seconds: int = Field(
        ...,
        ge=1,
        le=86400,
        description="Czas oczekiwania w sekundach (1 sec - 24h)"
    )


class ExportPDFNodeConfig(BaseModel):
    """
    Konfiguracja węzła Export PDF.

    Generuje PDF report z wyników workflow.

    Sections:
    - personas: Profil person
    - survey_results: Wyniki ankiety
    - focus_group_summary: Podsumowanie focus group
    - analysis: Analiza AI

    Options:
    - include_raw_data: Czy dołączyć surowe dane (appendix)

    Tier limits:
    - Free: Forced watermark
    - Pro: No watermark
    - Enterprise: White-label exports

    Przykład:
    {
      "report_title": "Mobile App Research Report",
      "sections": ["personas", "survey_results", "focus_group_summary"],
      "include_raw_data": false
    }
    """

    report_title: str = Field(..., min_length=1, max_length=255)
    sections: list[str] = Field(
        default_factory=lambda: ["personas", "survey_results", "focus_group_summary"],
        description="Sekcje do włączenia w raporcie"
    )
    include_raw_data: bool = Field(
        default=False,
        description="Czy dołączyć surowe dane (appendix)"
    )


class WebhookNodeConfig(BaseModel):
    """
    Konfiguracja węzła Webhook.

    ⚠️ OUT OF SCOPE MVP - ENTERPRISE ONLY

    POST workflow results do external URL.

    Security:
    - Tylko HTTPS URLs (HTTP blocked)
    - Tylko POST method w MVP
    - Max timeout: 60s
    - Max retries: 5

    Tier limit: Enterprise tylko

    Przykład:
    {
      "url": "https://api.client.com/workflow-completed",
      "method": "POST",
      "headers": {
        "Authorization": "Bearer token",
        "Content-Type": "application/json"
      },
      "payload_template": {
        "project_id": "{{context.project_id}}",
        "results": "{{context.analysis_report}}"
      }
    }
    """

    url: HttpUrl = Field(..., description="URL endpointu do POST request (HTTPS only)")
    method: Literal["POST"] = Field(default="POST")
    headers: dict[str, str] | None = Field(None, description="Custom headers")
    payload_template: dict | None = Field(
        None,
        description="Template payload (z placeholders dla workflow data)"
    )


class ConditionNodeConfig(BaseModel):
    """
    Konfiguracja węzła Condition (multi-branch logic).

    ⚠️ OUT OF SCOPE MVP - SIMPLIFIED

    Similar do Decision ale z multiple branches (3-5 outcomes).
    MVP: Użyj Decision node zamiast tego.

    Przykład (future):
    {
      "conditions": [
        {
          "condition": "sentiment.positive >= 80",
          "label": "Very Positive",
          "next_node_id": "node-xyz"
        },
        {
          "condition": "sentiment.positive >= 60",
          "label": "Positive",
          "next_node_id": "node-abc"
        }
      ],
      "default_branch_label": "Neutral/Mixed"
    }
    """

    conditions: list[dict] = Field(
        ...,
        description="Lista warunków [{condition: '...', label: '...', next_node_id: '...'}]"
    )
    default_branch_label: str = Field(default="Default", max_length=50)


class LoopNodeConfig(BaseModel):
    """
    Konfiguracja węzła Loop.

    ⚠️ OUT OF SCOPE MVP

    Iteruj przez array (np. każda persona osobno).
    MVP: Manual duplication zamiast loops.

    Przykład (future):
    {
      "iteration_source": "persona_ids",
      "max_iterations": 50
    }
    """

    iteration_source: str = Field(
        ...,
        description="Zmienna do iteracji (np. 'personas', 'survey_responses')"
    )
    max_iterations: int = Field(default=10, ge=1, le=100)


class MergeNodeConfig(BaseModel):
    """
    Konfiguracja węzła Merge (branch consolidation).

    Łączy multiple branches (po Decision/Condition) w jeden path.

    Merge strategies:
    - wait_all: Czekaj aż wszystkie branches complete (AND)
    - wait_any: Kontynuuj gdy ≥1 branch complete (OR)

    MVP: Tylko wait_all strategy

    Validation rules:
    - Merge node musi mieć ≥2 incoming edges

    Przykład:
    {
      "merge_strategy": "wait_all"
    }
    """

    merge_strategy: Literal["wait_all", "wait_any"] = Field(
        default="wait_all",
        description="wait_all: czekaj na wszystkie branches | wait_any: pierwszy który ukończy"
    )


# ==================== NODE CONFIG UNION TYPE ====================

# Union type dla wszystkich node configs (używany w node executors)
NodeConfig = (
    StartNodeConfig
    | EndNodeConfig
    | CreateProjectNodeConfig
    | GeneratePersonasNodeConfig
    | CreateSurveyNodeConfig
    | RunFocusGroupNodeConfig
    | AnalyzeResultsNodeConfig
    | DecisionNodeConfig
    | WaitNodeConfig
    | ExportPDFNodeConfig
    | WebhookNodeConfig
    | ConditionNodeConfig
    | LoopNodeConfig
    | MergeNodeConfig
)


# ==================== EXPORTS ====================

__all__ = [
    # Start/End Nodes
    "StartNodeConfig",
    "EndNodeConfig",
    # Core Action Nodes
    "CreateProjectNodeConfig",
    "GeneratePersonasNodeConfig",
    "CreateSurveyNodeConfig",
    "RunFocusGroupNodeConfig",
    "AnalyzeResultsNodeConfig",
    # Control Flow Nodes
    "DecisionNodeConfig",
    "WaitNodeConfig",
    # Integration Nodes
    "ExportPDFNodeConfig",
    "WebhookNodeConfig",
    # Advanced Logic Nodes
    "ConditionNodeConfig",
    "LoopNodeConfig",
    "MergeNodeConfig",
    # Union Type
    "NodeConfig",
]
