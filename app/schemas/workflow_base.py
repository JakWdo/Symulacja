"""
Podstawowe schematy Pydantic dla Workflow Builder - canvas, request/response, templates

Zawiera:
1. Canvas Data Schemas - CanvasNodePosition, CanvasNodeData, CanvasNode, CanvasEdge, CanvasData
2. Request Schemas - WorkflowCreate, WorkflowUpdate, WorkflowExecuteRequest
3. Response Schemas - WorkflowResponse, WorkflowExecutionResponse, ValidationResult
4. Template Schemas - WorkflowTemplateResponse, WorkflowInstantiateRequest, TemplateInstantiateRequest

Konwencje:
- Polish docstrings
- Field() z description dla każdego pola
- Validators gdzie potrzebne (canvas_data, edges)
- Config class z from_attributes=True dla response schemas
- Min/max constraints dla string lengths i int ranges
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, ValidationInfo


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


class WorkflowInstantiateRequest(BaseModel):
    """
    Request do utworzenia workflow z template.

    User wybiera template i tworzy nowy workflow na jego podstawie.
    template_id jest w path parametrze, nie w body.

    Pola:
    - project_id: UUID projektu (string lub UUID object - auto konwersja)
    - workflow_name: Custom nazwa (jeśli None - użyj template.name)

    Przykład request:
    POST /api/v1/workflows/templates/basic_research/instantiate
    {
      "project_id": "uuid-projektu",
      "workflow_name": "My Product Research"
    }
    """

    project_id: UUID = Field(..., description="UUID projektu (accepts string or UUID)")
    workflow_name: str | None = Field(
        None,
        description="Custom nazwa (jeśli None - użyj template.name)"
    )

    # Pydantic v2 automatic validation: str -> UUID conversion
    # Jeśli frontend wyśle string UUID, Pydantic automatycznie konwertuje
    # Jeśli string nie jest valid UUID, rzuci ValidationError z clear message


class TemplateInstantiateRequest(BaseModel):
    """
    DEPRECATED: Użyj WorkflowInstantiateRequest zamiast tego.

    Ten schema błędnie zawiera template_id w body, podczas gdy powinien być w path.

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


# ==================== EXPORTS ====================

__all__ = [
    # Canvas Data Schemas
    "CanvasNodePosition",
    "CanvasNodeData",
    "CanvasNode",
    "CanvasEdge",
    "CanvasData",
    # Request Schemas
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowExecuteRequest",
    # Response Schemas
    "WorkflowResponse",
    "WorkflowExecutionResponse",
    "ValidationResult",
    # Template Schemas
    "WorkflowTemplateResponse",
    "WorkflowInstantiateRequest",
    "TemplateInstantiateRequest",
]
