"""
StudyExecutor Service - Wykonanie zatwierdzonego planu badania.

Ten serwis:
1. Otrzymuje zatwierdzony plan z StudyDesignerSession.generated_plan
2. Parsuje execution_steps i tworzy workflow programmatically
3. Tworzy nodes i edges w canvas_data na podstawie execution_steps
4. Zapisuje workflow przez WorkflowService
5. Aktualizuje session status → executing
6. Zwraca created_workflow_id

Workflow jest tworzony jako "draft" i może być później wykonany
przez WorkflowExecutor lub ręcznie przez użytkownika.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_designer import StudyDesignerSession
from app.schemas.workflow import CanvasData, WorkflowCreate
from app.services.workflows.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class StudyExecutor:
    """Serwis wykonania zatwierdzonego planu badania."""

    def __init__(self, db: AsyncSession):
        """Inicjalizuje executor z database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.workflow_service = WorkflowService(db)
        logger.debug("StudyExecutor zainicjalizowany")

    async def execute_approved_plan(
        self, session: StudyDesignerSession, user_id: UUID
    ) -> UUID:
        """Wykonuje zatwierdzony plan badania poprzez stworzenie workflow.

        Args:
            session: StudyDesignerSession z zatwierdzonym planem
            user_id: UUID użytkownika wykonującego plan

        Returns:
            UUID utworzonego workflow

        Raises:
            HTTPException: 400 jeśli plan nie jest zatwierdzony lub brak execution_steps
        """
        logger.info(f"Executing approved plan for session {session.id}")

        # 1. Walidacja: czy plan jest zatwierdzony
        if session.status != "approved":
            raise HTTPException(
                status_code=400,
                detail=f"Session status is '{session.status}', must be 'approved' to execute",
            )

        if not session.generated_plan:
            raise HTTPException(
                status_code=400, detail="No plan generated for this session"
            )

        execution_steps = session.generated_plan.get("execution_steps")
        if not execution_steps:
            raise HTTPException(
                status_code=400,
                detail="Plan does not contain execution_steps - cannot create workflow",
            )

        # 2. Buduj canvas_data z execution_steps
        canvas_data = self._build_canvas_from_steps(execution_steps)

        # 3. Utwórz workflow przez WorkflowService
        workflow_name = self._generate_workflow_name(session)
        workflow_description = session.generated_plan.get(
            "markdown_summary", "Study designed via chat"
        )[:2000]  # Limit 2000 chars

        workflow_data = WorkflowCreate(
            name=workflow_name,
            description=workflow_description,
            project_id=session.project_id,
            canvas_data=canvas_data,
        )

        workflow = await self.workflow_service.create_workflow(workflow_data, user_id)

        # 4. Aktualizuj session: status = executing, created_workflow_id
        session.status = "executing"
        session.created_workflow_id = workflow.id
        await self.db.commit()

        logger.info(
            f"Workflow {workflow.id} created for session {session.id}, status updated to 'executing'"
        )

        return workflow.id

    def _build_canvas_from_steps(self, execution_steps: list[dict]) -> CanvasData:
        """Buduje canvas_data (nodes + edges) z execution_steps.

        Args:
            execution_steps: Lista kroków do wykonania
                [{"type": "personas_generation", "config": {...}}, ...]

        Returns:
            CanvasData z nodes i edges

        Przykład execution_steps:
        [
            {"type": "personas_generation", "config": {"num_personas": 20}},
            {"type": "focus_group_discussion", "config": {"num_questions": 5}},
            {"type": "ai_analysis", "config": {"analysis_type": "themes"}}
        ]
        """
        nodes = []
        edges = []

        # Start node (zawsze pierwszy)
        nodes.append(
            {
                "id": "node-start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "data": {"label": "Start", "config": {}},
            }
        )

        # Previous node ID dla łączenia edges
        prev_node_id = "node-start"
        y_offset = 100

        # Mapowanie execution step types do workflow node types
        step_type_mapping = {
            "personas_generation": "personas",
            "focus_group_discussion": "focus_groups",
            "survey_generation": "surveys",
            "ai_analysis": "analysis",
        }

        for idx, step in enumerate(execution_steps):
            step_type = step.get("type")
            step_config = step.get("config", {})

            # Mapuj step type do node type
            node_type = step_type_mapping.get(step_type, "custom")
            node_id = f"node-{idx + 1}"

            # Pozycja node (vertical layout)
            y_offset += 150
            position = {"x": 100, "y": y_offset}

            # Label (czytelna nazwa)
            label = self._get_node_label(step_type, step_config)

            # Utwórz node
            nodes.append(
                {
                    "id": node_id,
                    "type": node_type,
                    "position": position,
                    "data": {"label": label, "config": step_config},
                }
            )

            # Utwórz edge łączący z poprzednim nodem
            edges.append(
                {
                    "id": f"edge-{prev_node_id}-{node_id}",
                    "source": prev_node_id,
                    "target": node_id,
                }
            )

            prev_node_id = node_id

        # End node (zawsze ostatni)
        y_offset += 150
        nodes.append(
            {
                "id": "node-end",
                "type": "end",
                "position": {"x": 100, "y": y_offset},
                "data": {"label": "End", "config": {}},
            }
        )

        # Edge do end node
        edges.append(
            {
                "id": f"edge-{prev_node_id}-node-end",
                "source": prev_node_id,
                "target": "node-end",
            }
        )

        return CanvasData(nodes=nodes, edges=edges)

    def _get_node_label(self, step_type: str, config: dict[str, Any]) -> str:
        """Generuje czytelny label dla node na podstawie step type i config.

        Args:
            step_type: Typ kroku (personas_generation, focus_group_discussion, etc.)
            config: Konfiguracja kroku

        Returns:
            Czytelny label (np. "Generate 20 Personas")
        """
        if step_type == "personas_generation":
            num_personas = config.get("num_personas", 20)
            return f"Generate {num_personas} Personas"

        if step_type == "focus_group_discussion":
            num_questions = config.get("num_questions", 5)
            return f"Focus Group ({num_questions} questions)"

        if step_type == "survey_generation":
            num_questions = config.get("num_questions", 10)
            return f"Survey ({num_questions} questions)"

        if step_type == "ai_analysis":
            analysis_type = config.get("analysis_type", "general")
            return f"AI Analysis: {analysis_type.title()}"

        return step_type.replace("_", " ").title()

    def _generate_workflow_name(self, session: StudyDesignerSession) -> str:
        """Generuje nazwę workflow na podstawie session.

        Args:
            session: StudyDesignerSession

        Returns:
            Nazwa workflow (max 255 znaków)

        Przykład:
            "Study: Checkout Abandonment Research"
        """
        # Pobierz study_goal z conversation_state jeśli istnieje
        study_goal = session.conversation_state.get("study_goal")

        if study_goal:
            # Skróć do 200 znaków (prefix "Study: " ma 7 znaków)
            goal_truncated = (
                study_goal[:200] + "..." if len(study_goal) > 200 else study_goal
            )
            return f"Study: {goal_truncated}"

        # Fallback: użyj session ID
        return f"Study from Session {str(session.id)[:8]}"
