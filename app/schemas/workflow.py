"""
Schematy Pydantic dla Workflow Builder - walidacja API request/response

⚠️ UWAGA: Ten plik jest wrapperem dla backward compatibility.
Rzeczywista implementacja znajduje się w:
- workflow_base.py - Canvas data, Request/Response schemas, Templates
- workflow_nodes.py - 14 Node config schemas

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

Historia:
- PR4: Podział monolitycznego pliku (994 linie) na moduły dla łatwiejszego zarządzania
- Wrapper zapewnia backward compatibility - wszystkie importy działają bez zmian
"""

from __future__ import annotations

# Re-eksportuj wszystko z workflow_base
from app.schemas.workflow_base import (
    # Canvas Data Schemas
    CanvasNodePosition,
    CanvasNodeData,
    CanvasNode,
    CanvasEdge,
    CanvasData,
    # Request Schemas
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowExecuteRequest,
    # Response Schemas
    WorkflowResponse,
    WorkflowExecutionResponse,
    ValidationResult,
    # Template Schemas
    WorkflowTemplateResponse,
    WorkflowInstantiateRequest,
    TemplateInstantiateRequest,
)

# Re-eksportuj wszystko z workflow_nodes
from app.schemas.workflow_nodes import (
    # Start/End Nodes
    StartNodeConfig,
    EndNodeConfig,
    # Core Action Nodes
    CreateProjectNodeConfig,
    GeneratePersonasNodeConfig,
    CreateSurveyNodeConfig,
    RunFocusGroupNodeConfig,
    AnalyzeResultsNodeConfig,
    # Control Flow Nodes
    DecisionNodeConfig,
    WaitNodeConfig,
    # Integration Nodes
    ExportPDFNodeConfig,
    WebhookNodeConfig,
    # Advanced Logic Nodes
    ConditionNodeConfig,
    LoopNodeConfig,
    MergeNodeConfig,
    # Union Type
    NodeConfig,
)


# ==================== EXPORTS ====================

__all__ = [
    # Canvas Data Schemas (from workflow_base)
    "CanvasNodePosition",
    "CanvasNodeData",
    "CanvasNode",
    "CanvasEdge",
    "CanvasData",
    # Request Schemas (from workflow_base)
    "WorkflowCreate",
    "WorkflowUpdate",
    "WorkflowExecuteRequest",
    # Response Schemas (from workflow_base)
    "WorkflowResponse",
    "WorkflowExecutionResponse",
    "ValidationResult",
    # Template Schemas (from workflow_base)
    "WorkflowTemplateResponse",
    "WorkflowInstantiateRequest",
    "TemplateInstantiateRequest",
    # Start/End Nodes (from workflow_nodes)
    "StartNodeConfig",
    "EndNodeConfig",
    # Core Action Nodes (from workflow_nodes)
    "CreateProjectNodeConfig",
    "GeneratePersonasNodeConfig",
    "CreateSurveyNodeConfig",
    "RunFocusGroupNodeConfig",
    "AnalyzeResultsNodeConfig",
    # Control Flow Nodes (from workflow_nodes)
    "DecisionNodeConfig",
    "WaitNodeConfig",
    # Integration Nodes (from workflow_nodes)
    "ExportPDFNodeConfig",
    "WebhookNodeConfig",
    # Advanced Logic Nodes (from workflow_nodes)
    "ConditionNodeConfig",
    "LoopNodeConfig",
    "MergeNodeConfig",
    # Union Type (from workflow_nodes)
    "NodeConfig",
]
