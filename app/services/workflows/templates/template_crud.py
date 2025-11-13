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
            "description": "Prosty przepływ badawczy: goal → personas → survey → analiza → insights. Idealny dla początkujących.",
            "category": "research",
            "estimated_time_minutes": 4,
            "tags": ["personas", "survey", "quick", "beginner"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "workflowNode",
                        "position": {"x": 100, "y": 250},
                        "data": {
                            "label": "Start",
                            "type": "start",
                            "description": "Początek workflow",
                            "configured": True,
                            "config": {"trigger_type": "manual"},
                        },
                    },
                    {
                        "id": "goal-1",
                        "type": "workflowNode",
                        "position": {"x": 400, "y": 250},
                        "data": {
                            "label": "Research Goal",
                            "type": "goal",
                            "description": "Zdefiniuj cel badania",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "personas-1",
                        "type": "workflowNode",
                        "position": {"x": 700, "y": 250},
                        "data": {
                            "label": "Generate Personas",
                            "type": "persona",
                            "description": "Generuj AI personas",
                            "configured": False,
                            "config": {
                                "count": 20,
                                "demographic_preset": "millennials",
                                "target_audience_description": "Tech-savvy professionals",
                            },
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "workflowNode",
                        "position": {"x": 1000, "y": 250},
                        "data": {
                            "label": "Create Survey",
                            "type": "survey",
                            "description": "Ankieta dla person",
                            "configured": False,
                            "config": {
                                "survey_title": "Product Feedback Survey",
                                "template_id": "nps",
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "workflowNode",
                        "position": {"x": 1300, "y": 250},
                        "data": {
                            "label": "Analyze Results",
                            "type": "analysis",
                            "description": "AI analiza wyników",
                            "configured": False,
                            "config": {"analysis_type": "summary", "input_source": "survey"},
                        },
                    },
                    {
                        "id": "insights-1",
                        "type": "workflowNode",
                        "position": {"x": 1600, "y": 250},
                        "data": {
                            "label": "Insights",
                            "type": "insights",
                            "description": "Kluczowe wnioski",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "workflowNode",
                        "position": {"x": 1900, "y": 250},
                        "data": {
                            "label": "End",
                            "type": "end",
                            "description": "Zakończenie workflow",
                            "configured": True,
                            "config": {"success_message": "Research completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "goal-1"},
                    {"id": "e2", "source": "goal-1", "target": "personas-1"},
                    {"id": "e3", "source": "personas-1", "target": "survey-1"},
                    {"id": "e4", "source": "survey-1", "target": "analysis-1"},
                    {"id": "e5", "source": "analysis-1", "target": "insights-1"},
                    {"id": "e6", "source": "insights-1", "target": "end-1"},
                ],
            },
        },
        "deep_dive": {
            "id": "deep_dive",
            "name": "Deep Dive Research",
            "description": "Głęboka analiza: goal → personas → survey → focus group → analiza → insights. Dla zaawansowanych badań.",
            "category": "research",
            "estimated_time_minutes": 12,
            "tags": ["personas", "survey", "focus-group", "advanced"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "workflowNode",
                        "position": {"x": 100, "y": 250},
                        "data": {
                            "label": "Start",
                            "type": "start",
                            "description": "Początek workflow",
                            "configured": True,
                            "config": {"trigger_type": "manual"},
                        },
                    },
                    {
                        "id": "goal-1",
                        "type": "workflowNode",
                        "position": {"x": 400, "y": 250},
                        "data": {
                            "label": "Research Goal",
                            "type": "goal",
                            "description": "Cel deep dive research",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "personas-1",
                        "type": "workflowNode",
                        "position": {"x": 700, "y": 250},
                        "data": {
                            "label": "Generate Personas",
                            "type": "persona",
                            "description": "Generuj AI personas",
                            "configured": False,
                            "config": {"count": 20, "demographic_preset": "gen_z"},
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "workflowNode",
                        "position": {"x": 1000, "y": 250},
                        "data": {
                            "label": "Initial Survey",
                            "type": "survey",
                            "description": "Ankieta wstępna",
                            "configured": False,
                            "config": {"survey_title": "Pre-Focus Group Survey"},
                        },
                    },
                    {
                        "id": "focus-group-1",
                        "type": "workflowNode",
                        "position": {"x": 1300, "y": 250},
                        "data": {
                            "label": "Focus Group Discussion",
                            "type": "focus-group",
                            "description": "Dyskusja grupowa",
                            "configured": False,
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
                        "type": "workflowNode",
                        "position": {"x": 1600, "y": 250},
                        "data": {
                            "label": "Comprehensive Analysis",
                            "type": "analysis",
                            "description": "Głęboka analiza AI",
                            "configured": False,
                            "config": {
                                "analysis_type": "themes",
                                "input_source": "focus_group",
                            },
                        },
                    },
                    {
                        "id": "insights-1",
                        "type": "workflowNode",
                        "position": {"x": 1900, "y": 250},
                        "data": {
                            "label": "Insights",
                            "type": "insights",
                            "description": "Kluczowe wnioski",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "workflowNode",
                        "position": {"x": 2200, "y": 250},
                        "data": {
                            "label": "End",
                            "type": "end",
                            "description": "Zakończenie workflow",
                            "configured": True,
                            "config": {"success_message": "Deep dive completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "goal-1"},
                    {"id": "e2", "source": "goal-1", "target": "personas-1"},
                    {"id": "e3", "source": "personas-1", "target": "survey-1"},
                    {"id": "e4", "source": "survey-1", "target": "focus-group-1"},
                    {"id": "e5", "source": "focus-group-1", "target": "analysis-1"},
                    {"id": "e6", "source": "analysis-1", "target": "insights-1"},
                    {"id": "e7", "source": "insights-1", "target": "end-1"},
                ],
            },
        },
        "iterative_validation": {
            "id": "iterative_validation",
            "name": "Iterative Validation",
            "description": "Walidacja iteracyjna: goal → personas → survey → analiza → decision → insights. Dla testów A/B.",
            "category": "validation",
            "estimated_time_minutes": 18,
            "tags": ["personas", "survey", "decision", "iterative"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "workflowNode",
                        "position": {"x": 100, "y": 250},
                        "data": {
                            "label": "Start",
                            "type": "start",
                            "description": "Początek workflow",
                            "configured": True,
                            "config": {"trigger_type": "manual"},
                        },
                    },
                    {
                        "id": "goal-1",
                        "type": "workflowNode",
                        "position": {"x": 400, "y": 250},
                        "data": {
                            "label": "Research Goal",
                            "type": "goal",
                            "description": "Cel walidacji",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "personas-1",
                        "type": "workflowNode",
                        "position": {"x": 700, "y": 250},
                        "data": {
                            "label": "Generate Personas",
                            "type": "persona",
                            "description": "Generuj personas do walidacji",
                            "configured": False,
                            "config": {"count": 15},
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "workflowNode",
                        "position": {"x": 1000, "y": 250},
                        "data": {
                            "label": "Validation Survey",
                            "type": "survey",
                            "description": "Ankieta walidacyjna",
                            "configured": False,
                            "config": {
                                "survey_title": "Validation Survey",
                                "questions": ["Feedback", "Concerns"],
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "workflowNode",
                        "position": {"x": 1300, "y": 250},
                        "data": {
                            "label": "Analyze Feedback",
                            "type": "analysis",
                            "description": "Analiza feedbacku",
                            "configured": False,
                            "config": {
                                "analysis_type": "summary",
                                "input_source": "survey",
                            },
                        },
                    },
                    {
                        "id": "decision-1",
                        "type": "workflowNode",
                        "position": {"x": 1600, "y": 250},
                        "data": {
                            "label": "Check Positive %",
                            "type": "decision",
                            "description": "Decision point",
                            "configured": False,
                            "config": {
                                "condition": "positive_percent >= 70",
                                "true_branch_label": "Good Enough",
                                "false_branch_label": "Need More Data",
                            },
                        },
                    },
                    {
                        "id": "insights-1",
                        "type": "workflowNode",
                        "position": {"x": 1900, "y": 250},
                        "data": {
                            "label": "Insights",
                            "type": "insights",
                            "description": "Wnioski z walidacji",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "workflowNode",
                        "position": {"x": 2200, "y": 250},
                        "data": {
                            "label": "End",
                            "type": "end",
                            "description": "Zakończenie workflow",
                            "configured": True,
                            "config": {"success_message": "Validation completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "goal-1"},
                    {"id": "e2", "source": "goal-1", "target": "personas-1"},
                    {"id": "e3", "source": "personas-1", "target": "survey-1"},
                    {"id": "e4", "source": "survey-1", "target": "analysis-1"},
                    {"id": "e5", "source": "analysis-1", "target": "decision-1"},
                    {"id": "e6", "source": "decision-1", "target": "insights-1"},
                    {"id": "e7", "source": "insights-1", "target": "end-1"},
                ],
            },
        },
        "brand_perception": {
            "id": "brand_perception",
            "name": "Brand Perception Study",
            "description": "Percepcja marki: goal → personas → focus group → analiza → insights. Dla działów marketingu.",
            "category": "research",
            "estimated_time_minutes": 7,
            "tags": ["brand", "focus-group", "perception", "marketing"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "workflowNode",
                        "position": {"x": 100, "y": 250},
                        "data": {
                            "label": "Start",
                            "type": "start",
                            "description": "Początek workflow",
                            "configured": True,
                            "config": {"trigger_type": "manual"},
                        },
                    },
                    {
                        "id": "goal-1",
                        "type": "workflowNode",
                        "position": {"x": 400, "y": 250},
                        "data": {
                            "label": "Research Goal",
                            "type": "goal",
                            "description": "Cel badania marki",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "personas-1",
                        "type": "workflowNode",
                        "position": {"x": 700, "y": 250},
                        "data": {
                            "label": "Generate Target Audience",
                            "type": "persona",
                            "description": "Szeroka baza konsumentów",
                            "configured": False,
                            "config": {
                                "count": 25,
                                "demographic_preset": "all_ages",
                                "target_audience_description": "Broad consumer base",
                            },
                        },
                    },
                    {
                        "id": "focus-group-1",
                        "type": "workflowNode",
                        "position": {"x": 1000, "y": 250},
                        "data": {
                            "label": "Brand Discussion",
                            "type": "focus-group",
                            "description": "Dyskusja o marce",
                            "configured": False,
                            "config": {
                                "focus_group_title": "Brand Perception Discussion",
                                "topics": [
                                    "How familiar are you with our brand?",
                                    "What words come to mind when you think of our brand?",
                                    "How likely are you to recommend us?",
                                ],
                                "moderator_style": "neutral",
                                "rounds": 2,
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "workflowNode",
                        "position": {"x": 1300, "y": 250},
                        "data": {
                            "label": "Brand Sentiment Analysis",
                            "type": "analysis",
                            "description": "Analiza sentymentu marki",
                            "configured": False,
                            "config": {"analysis_type": "sentiment", "input_source": "focus_group"},
                        },
                    },
                    {
                        "id": "insights-1",
                        "type": "workflowNode",
                        "position": {"x": 1600, "y": 250},
                        "data": {
                            "label": "Insights",
                            "type": "insights",
                            "description": "Wnioski o marce",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "workflowNode",
                        "position": {"x": 1900, "y": 250},
                        "data": {
                            "label": "End",
                            "type": "end",
                            "description": "Zakończenie workflow",
                            "configured": True,
                            "config": {"success_message": "Brand study completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "goal-1"},
                    {"id": "e2", "source": "goal-1", "target": "personas-1"},
                    {"id": "e3", "source": "personas-1", "target": "focus-group-1"},
                    {"id": "e4", "source": "focus-group-1", "target": "analysis-1"},
                    {"id": "e5", "source": "analysis-1", "target": "insights-1"},
                    {"id": "e6", "source": "insights-1", "target": "end-1"},
                ],
            },
        },
        "user_journey": {
            "id": "user_journey",
            "name": "User Journey Mapping",
            "description": "Mapowanie ścieżki: goal → personas → survey → focus group → analiza → insights. Dla UX/product teams.",
            "category": "research",
            "estimated_time_minutes": 15,
            "tags": ["journey", "survey", "focus-group", "ux"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "workflowNode",
                        "position": {"x": 100, "y": 250},
                        "data": {
                            "label": "Start",
                            "type": "start",
                            "description": "Początek workflow",
                            "configured": True,
                            "config": {"trigger_type": "manual"},
                        },
                    },
                    {
                        "id": "goal-1",
                        "type": "workflowNode",
                        "position": {"x": 400, "y": 250},
                        "data": {
                            "label": "Research Goal",
                            "type": "goal",
                            "description": "Cel mapowania ścieżki",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "personas-1",
                        "type": "workflowNode",
                        "position": {"x": 700, "y": 250},
                        "data": {
                            "label": "Generate User Personas",
                            "type": "persona",
                            "description": "Aktywni użytkownicy",
                            "configured": False,
                            "config": {
                                "count": 15,
                                "demographic_preset": "users",
                                "target_audience_description": "Active users",
                            },
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "workflowNode",
                        "position": {"x": 1000, "y": 250},
                        "data": {
                            "label": "Journey Survey",
                            "type": "survey",
                            "description": "Ankieta o doświadczeniach",
                            "configured": False,
                            "config": {
                                "survey_title": "User Journey Survey",
                                "questions": ["Key touchpoints", "Pain points"],
                            },
                        },
                    },
                    {
                        "id": "focus-group-1",
                        "type": "workflowNode",
                        "position": {"x": 1300, "y": 250},
                        "data": {
                            "label": "Journey Discussion",
                            "type": "focus-group",
                            "description": "Dyskusja o ścieżce",
                            "configured": False,
                            "config": {
                                "focus_group_title": "Customer Journey Mapping",
                                "topics": [
                                    "Onboarding experience",
                                    "Key touchpoints",
                                    "Pain points",
                                    "Moments of delight",
                                ],
                                "moderator_style": "neutral",
                                "rounds": 3,
                            },
                        },
                    },
                    {
                        "id": "analysis-1",
                        "type": "workflowNode",
                        "position": {"x": 1600, "y": 250},
                        "data": {
                            "label": "Journey Analysis",
                            "type": "analysis",
                            "description": "Analiza ścieżki",
                            "configured": False,
                            "config": {
                                "analysis_type": "themes",
                                "input_source": "focus_group",
                            },
                        },
                    },
                    {
                        "id": "insights-1",
                        "type": "workflowNode",
                        "position": {"x": 1900, "y": 250},
                        "data": {
                            "label": "Insights",
                            "type": "insights",
                            "description": "Kluczowe wnioski",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "workflowNode",
                        "position": {"x": 2200, "y": 250},
                        "data": {
                            "label": "End",
                            "type": "end",
                            "description": "Zakończenie workflow",
                            "configured": True,
                            "config": {"success_message": "Journey mapping completed!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "goal-1"},
                    {"id": "e2", "source": "goal-1", "target": "personas-1"},
                    {"id": "e3", "source": "personas-1", "target": "survey-1"},
                    {"id": "e4", "source": "survey-1", "target": "focus-group-1"},
                    {"id": "e5", "source": "focus-group-1", "target": "analysis-1"},
                    {"id": "e6", "source": "analysis-1", "target": "insights-1"},
                    {"id": "e7", "source": "insights-1", "target": "end-1"},
                ],
            },
        },
        "feature_prioritization": {
            "id": "feature_prioritization",
            "name": "Feature Prioritization",
            "description": "Priorytetyzacja: goal → personas → survey → analiza → insights → decision. Dla product teams.",
            "category": "optimization",
            "estimated_time_minutes": 10,
            "tags": ["features", "survey", "decision", "product"],
            "canvas_data": {
                "nodes": [
                    {
                        "id": "start-1",
                        "type": "workflowNode",
                        "position": {"x": 100, "y": 250},
                        "data": {
                            "label": "Start",
                            "type": "start",
                            "description": "Początek workflow",
                            "configured": True,
                            "config": {"trigger_type": "manual"},
                        },
                    },
                    {
                        "id": "goal-1",
                        "type": "workflowNode",
                        "position": {"x": 400, "y": 250},
                        "data": {
                            "label": "Research Goal",
                            "type": "goal",
                            "description": "Cel priorytetyzacji",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "personas-1",
                        "type": "workflowNode",
                        "position": {"x": 700, "y": 250},
                        "data": {
                            "label": "Generate User Base",
                            "type": "persona",
                            "description": "Power users",
                            "configured": False,
                            "config": {"count": 30, "demographic_preset": "power_users"},
                        },
                    },
                    {
                        "id": "survey-1",
                        "type": "workflowNode",
                        "position": {"x": 1000, "y": 250},
                        "data": {
                            "label": "Feature Rating Survey",
                            "type": "survey",
                            "description": "Ankieta oceny funkcji",
                            "configured": False,
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
                        "type": "workflowNode",
                        "position": {"x": 1300, "y": 250},
                        "data": {
                            "label": "Priority Analysis",
                            "type": "analysis",
                            "description": "Analiza priorytetów",
                            "configured": False,
                            "config": {"analysis_type": "summary", "input_source": "survey"},
                        },
                    },
                    {
                        "id": "insights-1",
                        "type": "workflowNode",
                        "position": {"x": 1600, "y": 250},
                        "data": {
                            "label": "Insights",
                            "type": "insights",
                            "description": "Kluczowe wnioski",
                            "configured": False,
                            "config": {},
                        },
                    },
                    {
                        "id": "decision-1",
                        "type": "workflowNode",
                        "position": {"x": 1900, "y": 250},
                        "data": {
                            "label": "Select Top 3",
                            "type": "decision",
                            "description": "Wybór top 3 funkcji",
                            "configured": False,
                            "config": {
                                "condition": "rank <= 3",
                                "true_branch_label": "Priority Features",
                                "false_branch_label": "Backlog",
                            },
                        },
                    },
                    {
                        "id": "end-1",
                        "type": "workflowNode",
                        "position": {"x": 2200, "y": 250},
                        "data": {
                            "label": "End",
                            "type": "end",
                            "description": "Zakończenie workflow",
                            "configured": True,
                            "config": {"success_message": "Top features identified!"},
                        },
                    },
                ],
                "edges": [
                    {"id": "e1", "source": "start-1", "target": "goal-1"},
                    {"id": "e2", "source": "goal-1", "target": "personas-1"},
                    {"id": "e3", "source": "personas-1", "target": "survey-1"},
                    {"id": "e4", "source": "survey-1", "target": "analysis-1"},
                    {"id": "e5", "source": "analysis-1", "target": "insights-1"},
                    {"id": "e6", "source": "insights-1", "target": "decision-1"},
                    {"id": "e7", "source": "decision-1", "target": "end-1"},
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
