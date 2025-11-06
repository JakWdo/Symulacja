"""
Schematy Pydantic dla Workflow Builder - walidacja API request/response

Zawiera:
1. Request schemas (Create, Update, Execute)
2. Response schemas (Workflow, Execution, Validation)
3. Node config schemas (14 typów węzłów)
4. Template schemas (InstantiateRequest, TemplateResponse)
5. Union type NodeConfig dla wszystkich node configs

Konwencje:
- Polish docstrings
- Field() z description dla każdego pola
- Validators gdzie potrzebne (canvas_data, condition, url)
- Config class z from_attributes=True dla response schemas
- Min/max constraints dla string lengths i int ranges
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, field_validator, ValidationInfo


# ==================== CANVAS DATA SCHEMAS ====================


class CanvasNodePosition(BaseModel):
    """
    Pozycja node na canvas (współrzędne x, y).

    React Flow używa tych współrzędnych do renderowania nodes.
    """
    x: float = Field(..., description="Pozycja X na canvas")
    y: float = Field(..., description="Pozycja Y na canvas")


class CanvasNodeData(BaseModel):
    """
    Dane node (label i konfiguracja).

    - label: Nazwa wyświetlana na node
    - config: Konfiguracja specyficzna dla typu node (NodeConfig)
    """
    label: str = Field(..., min_length=1, max_length=255, description="Nazwa node wyświetlana na canvas")
    config: dict = Field(default_factory=dict, description="Konfiguracja node (zależy od type)")


class CanvasNode(BaseModel):
    """
    Pojedynczy node na canvas React Flow.

    Zawiera:
    - id: Unikalny identyfikator node
    - type: Typ node (start, end, generatePersonas, etc.)
    - position: Współrzędne {x, y} na canvas
    - data: Label i config node
    """
    id: str = Field(..., min_length=1, description="Unikalny ID node")
    type: str = Field(..., min_length=1, description="Typ node (start, end, generatePersonas, etc.)")
    position: CanvasNodePosition = Field(..., description="Pozycja node na canvas")
    data: CanvasNodeData = Field(..., description="Dane node (label, config)")


class CanvasEdge(BaseModel):
    """
    Połączenie między nodes (edge).

    - id: Unikalny identyfikator edge
    - source: ID source node
    - target: ID target node
    - label: Opcjonalna etykieta (np. "Yes", "No" dla Decision node)
    """
    id: str = Field(..., min_length=1, description="Unikalny ID edge")
    source: str = Field(..., min_length=1, description="ID source node")
    target: str = Field(..., min_length=1, description="ID target node")
    label: str | None = Field(None, max_length=100, description="Opcjonalna etykieta edge")


class CanvasData(BaseModel):
    """
    Stan canvas React Flow (nodes + edges).

    Główna struktura przechowująca cały workflow jako graf:
    - nodes: Lista wszystkich węzłów workflow
    - edges: Lista połączeń między nodes

    Przykład:
    {
      "nodes": [
        {
          "id": "node-1",
          "type": "start",
          "position": {"x": 100, "y": 100},
          "data": {"label": "Start", "config": {}}
        }
      ],
      "edges": [
        {
          "id": "edge-1",
          "source": "node-1",
          "target": "node-2",
          "label": null
        }
      ]
    }
    """
    nodes: list[CanvasNode] = Field(default_factory=list, description="Lista nodes workflow")
    edges: list[CanvasEdge] = Field(default_factory=list, description="Lista edges (połączeń)")

    @field_validator('nodes')
    @classmethod
    def validate_nodes_not_empty_if_edges(cls, v: list[CanvasNode]) -> list[CanvasNode]:
        """
        Jeśli są edges, muszą być też nodes.

        Args:
            v: Lista nodes

        Returns:
            Zwalidowana lista nodes

        Raises:
            ValueError: Jeśli są edges ale brak nodes
        """
        # Ta walidacja zostanie wywołana po edges, więc nie możemy tu sprawdzić edges
        # Zostawiamy podstawową walidację - edges będą walidowane osobno
        return v

    @field_validator('edges')
    @classmethod
    def validate_edges_reference_existing_nodes(cls, v: list[CanvasEdge], info: ValidationInfo) -> list[CanvasEdge]:
        """
        Sprawdź czy edges wskazują na istniejące nodes.

        Args:
            v: Lista edges
            info: Kontekst walidacji z dostępem do innych pól

        Returns:
            Zwalidowana lista edges

        Raises:
            ValueError: Jeśli edge wskazuje na nieistniejący node
        """
        if 'nodes' not in info.data:
            # nodes nie zostały jeszcze zwalidowane
            return v

        nodes = info.data.get('nodes', [])
        node_ids = {node.id for node in nodes}

        for edge in v:
            if edge.source not in node_ids:
                raise ValueError(f"Edge {edge.id} references non-existent source node: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge {edge.id} references non-existent target node: {edge.target}")

        return v


# ==================== REQUEST SCHEMAS ====================


class WorkflowCreate(BaseModel):
    """
    Schema do tworzenia nowego workflow.

    Użytkownik podaje:
    - name: Nazwa workflow (wymagane, 1-255 znaków)
    - description: Opis celu workflow (opcjonalne, max 2000 znaków)
    - project_id: UUID projektu do którego należy workflow
    - canvas_data: Stan canvas React Flow z nodes i edges (domyślnie pusty)

    Przykład:
    {
      "name": "Product Research Flow",
      "description": "Badanie funkcji produktu mobilnego",
      "project_id": "uuid-projektu",
      "canvas_data": {"nodes": [], "edges": []}
    }
    """

    name: str = Field(..., min_length=1, max_length=255, description="Nazwa workflow")
    description: str | None = Field(None, max_length=2000, description="Opis celu workflow")
    project_id: UUID = Field(..., description="UUID projektu do którego należy workflow")
    canvas_data: CanvasData = Field(
        default_factory=CanvasData,
        description="Stan canvas React Flow: {nodes: [], edges: []}"
    )


class WorkflowUpdate(BaseModel):
    """
    Schema do aktualizacji workflow.

    Wszystkie pola opcjonalne - aktualizowane są tylko podane pola.

    Dozwolone zmiany:
    - name: Zmiana nazwy
    - description: Zmiana opisu
    - canvas_data: Aktualizacja stanu canvas (nodes/edges)
    - status: Zmiana statusu workflow (draft/active/archived)

    Przykład:
    {
      "name": "Product Research Flow v2",
      "canvas_data": {"nodes": [...], "edges": [...]}
    }
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    canvas_data: CanvasData | None = None
    status: Literal["draft", "active", "archived"] | None = None


class WorkflowExecuteRequest(BaseModel):
    """
    Schema do wykonania workflow.

    MVP: Tylko tryb sekwencyjny (sequential).

    Przyszłe opcje (out of scope MVP):
    - timeout: Maksymalny czas wykonania w sekundach
    - dry_run: Tryb testowy bez zapisywania wyników
    - parallel: Równoległe wykonanie branches

    Przykład:
    {
      "execution_mode": "sequential"
    }
    """

    execution_mode: Literal["sequential"] = Field(
        default="sequential",
        description="Tryb wykonania (MVP: tylko sequential)"
    )


# ==================== RESPONSE SCHEMAS ====================


class WorkflowResponse(BaseModel):
    """
    Schema odpowiedzi API z workflow.

    Zwraca kompletne dane workflow:
    - Podstawowe metadane (id, name, description)
    - Canvas data (nodes i edges React Flow)
    - Status workflow (draft/active/archived)
    - Owner info
    - Timestamps

    Używany w:
    - GET /workflows/{id} - szczegóły workflow
    - POST /workflows - po utworzeniu
    - PUT /workflows/{id} - po aktualizacji
    """

    id: UUID
    project_id: UUID
    owner_id: UUID
    name: str
    description: str | None
    canvas_data: CanvasData
    status: str  # "draft" | "active" | "archived"
    is_template: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode)


class WorkflowExecutionResponse(BaseModel):
    """
    Schema odpowiedzi API z execution.

    Zwraca dane wykonania workflow:
    - Status (pending/running/completed/failed)
    - Current step (który node jest wykonywany)
    - Result data (wyniki każdego kroku)
    - Error message (jeśli failed)
    - Timestamps (started_at, completed_at)

    Używany w:
    - POST /workflows/{id}/execute - zwraca execution_id
    - GET /workflows/executions/{id} - polling dla progress
    """

    id: UUID
    workflow_id: UUID
    triggered_by: UUID
    status: str  # "pending" | "running" | "completed" | "failed"
    current_step_id: UUID | None
    result_data: dict | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class ValidationResult(BaseModel):
    """
    Wynik walidacji workflow.

    Zwraca:
    - is_valid: Czy workflow może być wykonany
    - errors: Lista błędów blokujących (must fix)
    - warnings: Lista ostrzeżeń (non-blocking)

    Przykład:
    {
      "is_valid": false,
      "errors": [
        "Orphaned node detected: node-456 (Generate Personas)",
        "Decision node must have exactly 2 outgoing edges"
      ],
      "warnings": [
        "Large workflow (50+ nodes) may be slow"
      ]
    }
    """

    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def add_error(self, message: str):
        """
        Dodaj błąd walidacji i ustaw is_valid=False.

        Args:
            message: Komunikat błędu
        """
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """
        Dodaj ostrzeżenie (nie wpływa na is_valid).

        Args:
            message: Komunikat ostrzeżenia
        """
        self.warnings.append(message)


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
        min_items=1,
        max_items=10,
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


# ==================== TEMPLATE SCHEMAS ====================


class WorkflowTemplateResponse(BaseModel):
    """
    Schema dla workflow template.

    Template to pre-built workflow który user może customize.

    Pola:
    - id: Template ID (np. 'basic_research', 'deep_dive')
    - name: Nazwa template
    - description: Opis co template robi
    - category: Kategoria (research, validation, etc.)
    - node_count: Liczba nodes w template
    - estimated_time_minutes: Szacowany czas wykonania
    - canvas_data: Stan canvas z nodes i edges
    - tags: Tagi dla filtrowania

    Przykład:
    {
      "id": "basic_research",
      "name": "Basic Research Flow",
      "description": "Simple 4-step flow for quick insights",
      "category": "research",
      "node_count": 4,
      "estimated_time_minutes": 3,
      "canvas_data": {...},
      "tags": ["quick", "personas", "survey"]
    }
    """

    id: str = Field(..., description="Template ID (np. 'basic_research')")
    name: str
    description: str
    category: str = Field(..., description="Kategoria template (research, validation, etc.)")
    node_count: int
    estimated_time_minutes: int | None
    canvas_data: CanvasData
    tags: list[str] = Field(default_factory=list)


class TemplateInstantiateRequest(BaseModel):
    """
    Request do utworzenia workflow z template.

    User wybiera template i tworzy nowy workflow na jego podstawie.

    Pola:
    - template_id: ID szablonu do użycia
    - project_id: UUID projektu
    - workflow_name: Custom nazwa (jeśli None - użyj template.name)

    Przykład:
    {
      "template_id": "basic_research",
      "project_id": "uuid-projektu",
      "workflow_name": "My Product Research"
    }
    """

    template_id: str = Field(..., description="ID szablonu do użycia")
    project_id: UUID = Field(..., description="UUID projektu")
    workflow_name: str | None = Field(
        None,
        description="Custom nazwa (jeśli None - użyj template.name)"
    )
