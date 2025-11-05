"""
Schematy Pydantic dla walidacji danych (request/response)

Ten pakiet zawiera modele Pydantic używane do:
1. Walidacji danych wejściowych (request schemas) - co API przyjmuje
2. Serializacji odpowiedzi (response schemas) - co API zwraca
3. Transformacji danych między warstwami aplikacji

Pydantic automatycznie:
- Waliduje typy danych
- Konwertuje typy (np. string -> int)
- Generuje błędy walidacji
- Tworzy dokumentację OpenAPI/Swagger

Pliki:
- project.py - schematy dla projektów badawczych
- persona.py - schematy dla person
- focus_group.py - schematy dla grup fokusowych
- survey.py - schematy dla ankiet syntetycznych
- graph.py - schematy dla analizy grafowej
- workflow.py - schematy dla workflow builder (14 node types)
"""

# Workflow schemas exports
from app.schemas.workflow import (
    # Request schemas
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecuteRequest,
    # Response schemas
    WorkflowResponse,
    WorkflowExecutionResponse,
    ValidationResult,
    # Node config schemas (14 types)
    StartNodeConfig,
    EndNodeConfig,
    CreateProjectNodeConfig,
    GeneratePersonasNodeConfig,
    CreateSurveyNodeConfig,
    RunFocusGroupNodeConfig,
    AnalyzeResultsNodeConfig,
    DecisionNodeConfig,
    WaitNodeConfig,
    ExportPDFNodeConfig,
    WebhookNodeConfig,
    ConditionNodeConfig,
    LoopNodeConfig,
    MergeNodeConfig,
    # Union type
    NodeConfig,
    # Template schemas
    WorkflowTemplateResponse,
    TemplateInstantiateRequest,
)

__all__ = [
    # Workflow request schemas
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowExecuteRequest",
    # Workflow response schemas
    "WorkflowResponse",
    "WorkflowExecutionResponse",
    "ValidationResult",
    # Node config schemas
    "StartNodeConfig",
    "EndNodeConfig",
    "CreateProjectNodeConfig",
    "GeneratePersonasNodeConfig",
    "CreateSurveyNodeConfig",
    "RunFocusGroupNodeConfig",
    "AnalyzeResultsNodeConfig",
    "DecisionNodeConfig",
    "WaitNodeConfig",
    "ExportPDFNodeConfig",
    "WebhookNodeConfig",
    "ConditionNodeConfig",
    "LoopNodeConfig",
    "MergeNodeConfig",
    "NodeConfig",
    # Template schemas
    "WorkflowTemplateResponse",
    "TemplateInstantiateRequest",
]