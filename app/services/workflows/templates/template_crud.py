"""
Moduł CRUD dla Workflow Templates

Odpowiedzialny za:
- Przechowywanie hardcoded templates
- Pobieranie listy templates
- Pobieranie pojedynczego template po ID
- Tworzenie workflow z template
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowTemplateResponse
from .template_validator import WorkflowTemplateValidator


logger = logging.getLogger(__name__)


class WorkflowTemplateCRUD:
    """
    CRUD operations dla workflow templates

    Templates są hardcoded w TEMPLATES dict. Każdy template zawiera:
    - Predefiniowane nodes (React Flow format)
    - Predefiniowane edges (connections)
    - Metadata (name, description, category, tags)

    MVP: 6 templates zgodnych z PRD (workflow_builder_prd.md)
    """

    # Hardcoded templates (zgodnie z workflow_builder_prd.md)
    TEMPLATES = {
        "basic_research": {
            "id": "basic_research",
            "name": "Basic Research",
            "description": "Prosty przepływ badawczy: personas → survey → analiza. Idealny dla początkujących.",
            "category": "research",
            "estimated_time_minutes": 4,
            "tags": ["personas", "survey", "quick", "beginner"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start", "config": {"trigger_type": "manual"}},
                    },
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "label": "Generate Personas",
                            "config": {
                                "count": 20,
                                "demographic_preset": "millennials",
                                "target_audience_description": "Tech-savvy professionals",
                            },
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "create-survey",
                        "position": {"x": 100, "y": 300},
                        "data": {
                            "label": "Create Survey",
                            "config": {
                                "survey_title": "Product Feedback Survey",
                                "template_id": "nps",
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "analyze-results",
                        "position": {"x": 100, "y": 400},
                        "data": {
                            "label": "Analyze Results",
                            "config": {"analysis_type": "summary", "input_source": "survey"},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "end",
                        "position": {"x": 100, "y": 500},
                        "data": {
                            "label": "End",
                            "config": {"success_message": "Research completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "survey-1"},
                    {"id": "e3", "source": "survey-1", "target": "analysis-1"},
                    {"id": "e4", "source": "analysis-1", "target": "end-1"},
                ],
            },
        },
        "deep_dive": {
            "id": "deep_dive",
            "name": "Deep Dive Research",
            "description": "Głęboka analiza z focus group: personas → survey → focus group → analiza. Dla zaawansowanych badań.",
            "category": "research",
            "estimated_time_minutes": 12,
            "tags": ["personas", "survey", "focus-group", "advanced"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start", "config": {"trigger_type": "manual"}},
                    },
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "label": "Generate Personas",
                            "config": {"count": 20, "demographic_preset": "gen_z"},
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "create-survey",
                        "position": {"x": 100, "y": 300},
                        "data": {
                            "label": "Initial Survey",
                            "config": {"survey_title": "Pre-Focus Group Survey"},
                        },
                    },
                    {
                        "id": "focus-group-1",
                        "type": "run-focus-group",
                        "position": {"x": 100, "y": 400},
                        "data": {
                            "label": "Focus Group Discussion",
                            "config": {
                                "focus_group_title": "Deep Dive Discussion",
                                "topics": [
                                    "Pain points",
                                    "Feature requests",
                                    "Alternatives",
                                ],
                                "moderator_style": "probing",
                                "rounds": 3,
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "analyze-results",
                        "position": {"x": 100, "y": 500},
                        "data": {
                            "label": "Comprehensive Analysis",
                            "config": {
                                "analysis_type": "themes",
                                "input_source": "focus_group",
                            },
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "end",
                        "position": {"x": 100, "y": 600},
                        "data": {"label": "End", "config": {}},
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "survey-1"},
                    {"id": "e3", "source": "survey-1", "target": "focus-group-1"},
                    {"id": "e4", "source": "focus-group-1", "target": "analysis-1"},
                    {"id": "e5", "source": "analysis-1", "target": "end-1"},
                ],
            },
        },
        "iterative_validation": {
            "id": "iterative_validation",
            "name": "Iterative Validation",
            "description": "Iteracja z decision points: sprawdź positive feedback, jeśli <70% → generuj więcej person. Dla testów A/B.",
            "category": "validation",
            "estimated_time_minutes": 18,
            "tags": ["personas", "focus-group", "decision", "iterative"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "start",
                        "position": {"x": 50, "y": 50},
                        "data": {"label": "Start", "config": {}},
                    },
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "position": {"x": 50, "y": 150},
                        "data": {
                            "label": "Generate Initial Personas",
                            "config": {"count": 10},
                        },
                    },
                    {
                        "id": "focus-group-1",
                        "type": "run-focus-group",
                        "position": {"x": 50, "y": 250},
                        "data": {
                            "label": "Focus Group",
                            "config": {
                                "focus_group_title": "Validation Discussion",
                                "topics": ["Feedback", "Concerns"],
                            },
                        },
                    },
                    {
                        "id": "decision-1",
                        "type": "decision",
                        "position": {"x": 50, "y": 350},
                        "data": {
                            "label": "Check Positive %",
                            "config": {
                                "condition": "positive_percent >= 70",
                                "true_branch_label": "Good Enough",
                                "false_branch_label": "Need More Data",
                            },
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "end",
                        "position": {"x": 200, "y": 450},
                        "data": {"label": "Success", "config": {}},
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "focus-group-1"},
                    {"id": "e3", "source": "focus-group-1", "target": "decision-1"},
                    {"id": "e4-true", "source": "decision-1", "target": "end-1"},
                    # Loop back edge (jeśli False - można dodać w UI)
                    # {"id": "e4-false", "source": "decision-1", "target": "personas-1"}
                ],
            },
        },
        "brand_perception": {
            "id": "brand_perception",
            "name": "Brand Perception Study",
            "description": "Badanie percepcji marki: personas → survey (brand awareness + sentiment) → analiza. Dla działów marketingu.",
            "category": "research",
            "estimated_time_minutes": 7,
            "tags": ["brand", "survey", "perception", "marketing"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start", "config": {"trigger_type": "manual"}},
                    },
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "label": "Generate Target Audience",
                            "config": {
                                "count": 25,
                                "demographic_preset": "all_ages",
                                "target_audience_description": "Broad consumer base",
                            },
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "create-survey",
                        "position": {"x": 100, "y": 300},
                        "data": {
                            "label": "Brand Awareness Survey",
                            "config": {
                                "survey_title": "Brand Perception Study",
                                "template_id": "brand_awareness",
                                "questions": [
                                    "How familiar are you with our brand?",
                                    "What words come to mind when you think of our brand?",
                                    "How likely are you to recommend us?",
                                ],
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "analyze-results",
                        "position": {"x": 100, "y": 400},
                        "data": {
                            "label": "Brand Sentiment Analysis",
                            "config": {"analysis_type": "sentiment", "input_source": "survey"},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "end",
                        "position": {"x": 100, "y": 500},
                        "data": {
                            "label": "End",
                            "config": {"success_message": "Brand study completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "survey-1"},
                    {"id": "e3", "source": "survey-1", "target": "analysis-1"},
                    {"id": "e4", "source": "analysis-1", "target": "end-1"},
                ],
            },
        },
        "user_journey": {
            "id": "user_journey",
            "name": "User Journey Mapping",
            "description": "Customer journey analysis: personas → focus group (journey topics) → analiza → export PDF. Dla UX/product teams.",
            "category": "research",
            "estimated_time_minutes": 15,
            "tags": ["journey", "focus-group", "ux", "export"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start", "config": {"trigger_type": "manual"}},
                    },
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "label": "Generate User Personas",
                            "config": {
                                "count": 15,
                                "demographic_preset": "users",
                                "target_audience_description": "Active users",
                            },
                        },
                    },
                    {
                        "id": "focus-group-1",
                        "type": "run-focus-group",
                        "position": {"x": 100, "y": 300},
                        "data": {
                            "label": "Journey Discussion",
                            "config": {
                                "focus_group_title": "Customer Journey Mapping",
                                "topics": [
                                    "Onboarding experience",
                                    "Key touchpoints",
                                    "Pain points",
                                    "Moments of delight",
                                ],
                                "moderator_style": "exploratory",
                                "rounds": 4,
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "analyze-results",
                        "position": {"x": 100, "y": 400},
                        "data": {
                            "label": "Journey Analysis",
                            "config": {
                                "analysis_type": "journey_map",
                                "input_source": "focus_group",
                            },
                        },
                    },
                    {
                        "id": "export-1",
                        "type": "export-pdf",
                        "position": {"x": 100, "y": 500},
                        "data": {
                            "label": "Export Journey Map",
                            "config": {"template": "journey_map", "include_quotes": True},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "end",
                        "position": {"x": 100, "y": 600},
                        "data": {
                            "label": "End",
                            "config": {"success_message": "Journey map exported!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "focus-group-1"},
                    {"id": "e3", "source": "focus-group-1", "target": "analysis-1"},
                    {"id": "e4", "source": "analysis-1", "target": "export-1"},
                    {"id": "e5", "source": "export-1", "target": "end-1"},
                ],
            },
        },
        "feature_prioritization": {
            "id": "feature_prioritization",
            "name": "Feature Prioritization",
            "description": "Feature voting + prioritization: personas → survey (feature rating) → analiza → decision (top 3 features) → end. Dla product teams.",
            "category": "optimization",
            "estimated_time_minutes": 10,
            "tags": ["features", "survey", "decision", "product"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "start",
                        "position": {"x": 100, "y": 100},
                        "data": {"label": "Start", "config": {"trigger_type": "manual"}},
                    },
                    {
                        "id": "personas-1",
                        "type": "generate-personas",
                        "position": {"x": 100, "y": 200},
                        "data": {
                            "label": "Generate User Base",
                            "config": {"count": 30, "demographic_preset": "power_users"},
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "create-survey",
                        "position": {"x": 100, "y": 300},
                        "data": {
                            "label": "Feature Rating Survey",
                            "config": {
                                "survey_title": "Feature Prioritization",
                                "template_id": "feature_vote",
                                "questions": [
                                    "Rate Feature A (1-10)",
                                    "Rate Feature B (1-10)",
                                    "Rate Feature C (1-10)",
                                    "Rate Feature D (1-10)",
                                    "Rate Feature E (1-10)",
                                ],
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "analyze-results",
                        "position": {"x": 100, "y": 400},
                        "data": {
                            "label": "Priority Analysis",
                            "config": {"analysis_type": "ranking", "input_source": "survey"},
                        },
                    },
                    {
                        "id": "decision-1",
                        "type": "decision",
                        "position": {"x": 100, "y": 500},
                        "data": {
                            "label": "Select Top 3 Features",
                            "config": {
                                "condition": "rank <= 3",
                                "true_branch_label": "Priority Features",
                                "false_branch_label": "Backlog",
                            },
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "end",
                        "position": {"x": 100, "y": 600},
                        "data": {
                            "label": "End",
                            "config": {"success_message": "Top 3 features identified!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "personas-1"},
                    {"id": "e2", "source": "personas-1", "target": "survey-1"},
                    {"id": "e3", "source": "survey-1", "target": "analysis-1"},
                    {"id": "e4", "source": "analysis-1", "target": "decision-1"},
                    {"id": "e5", "source": "decision-1", "target": "end-1"},
                ],
            },
        },
    }

    def __init__(self):
        """Initialize template CRUD service"""
        logger.debug(
            f"WorkflowTemplateCRUD initialized with {len(self.TEMPLATES)} templates"
        )

    def get_templates(self) -> list[WorkflowTemplateResponse]:
        """
        Zwraca listę wszystkich dostępnych templates

        Returns:
            Lista WorkflowTemplateResponse objects posortowana po estimated_time_minutes
        """
        templates = []

        for template_id, template_data in self.TEMPLATES.items():
            templates.append(
                WorkflowTemplateResponse(
                    id=template_id,
                    name=template_data["name"],
                    description=template_data["description"],
                    category=template_data["category"],
                    node_count=len(template_data["canvas_data"]["nodes"]),
                    estimated_time_minutes=template_data.get("estimated_time_minutes"),
                    canvas_data=template_data["canvas_data"],
                    tags=template_data.get("tags", []),
                )
            )

        # Sortuj po czasie wykonania (od najszybszego)
        templates.sort(key=lambda t: t.estimated_time_minutes or 999)

        logger.info(f"Returning {len(templates)} workflow templates")
        return templates

    def get_template_by_id(self, template_id: str) -> WorkflowTemplateResponse | None:
        """
        Pobiera pojedynczy template po ID

        Args:
            template_id: ID template (np. "basic_research")

        Returns:
            WorkflowTemplateResponse lub None jeśli nie znaleziono
        """
        template_data = self.TEMPLATES.get(template_id)

        if not template_data:
            logger.warning(f"Template '{template_id}' not found")
            return None

        return WorkflowTemplateResponse(
            id=template_id,
            name=template_data["name"],
            description=template_data["description"],
            category=template_data["category"],
            node_count=len(template_data["canvas_data"]["nodes"]),
            estimated_time_minutes=template_data.get("estimated_time_minutes"),
            canvas_data=template_data["canvas_data"],
            tags=template_data.get("tags", []),
        )

    async def create_from_template(
        self,
        template_id: str,
        project_id: UUID,
        user_id: UUID,
        workflow_name: str | None,
        db: AsyncSession,
    ) -> Workflow:
        """
        Tworzy workflow z template

        Args:
            template_id: ID template do użycia
            project_id: UUID projektu
            user_id: UUID użytkownika (owner)
            workflow_name: Custom nazwa (jeśli None - użyj template name)
            db: Database session

        Returns:
            Utworzony Workflow object

        Raises:
            ValueError: Jeśli template nie istnieje
        """
        from app.schemas.workflow import WorkflowCreate
        from app.services.workflows.workflow_service import WorkflowService

        # Get template
        template = self.get_template_by_id(template_id)

        if not template:
            raise ValueError(f"Template '{template_id}' not found")

        # Prepare workflow data
        name = workflow_name or f"{template.name} (from template)"

        # Create workflow using WorkflowService
        workflow_service = WorkflowService(db)

        workflow_data = WorkflowCreate(
            name=name,
            description=template.description,
            project_id=project_id,
            canvas_data=template.canvas_data,
        )

        workflow = await workflow_service.create_workflow(data=workflow_data, user_id=user_id)

        logger.info(
            f"Created workflow '{workflow.name}' from template '{template_id}' for user {user_id}"
        )

        return workflow

    def validate_template(self, template_id: str) -> tuple[bool, list[str]]:
        """
        Waliduje template structure (start node, end node, valid edges)

        Deleguje do WorkflowTemplateValidator.

        Args:
            template_id: ID template do walidacji

        Returns:
            Tuple (is_valid, errors)
        """
        template_data = self.TEMPLATES.get(template_id)
        return WorkflowTemplateValidator.validate_template(template_id, template_data)

    def validate_all_templates(self) -> dict[str, tuple[bool, list[str]]]:
        """
        Waliduje wszystkie templates

        Deleguje do WorkflowTemplateValidator.

        Returns:
            Dict {template_id: (is_valid, errors)}
        """
        return WorkflowTemplateValidator.validate_all_templates(self.TEMPLATES)
