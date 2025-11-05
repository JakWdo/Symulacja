"""Executor dla node typu 'run-focus-group'.

Integracja z FocusGroupServiceLangChain dla prowadzenia focus groups w ramach workflow.
"""

import logging
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from app.models import FocusGroup, Persona
from app.schemas.workflow import RunFocusGroupNodeConfig
from app.services.focus_groups.focus_group_service_langchain import (
    FocusGroupServiceLangChain
)
from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class RunFocusGroupExecutor(NodeExecutor):
    """Executor dla prowadzenia focus group w workflow.

    Flow:
    1. Pobierz participant_ids (z config lub poprzedniego generate-personas node)
    2. Stwórz FocusGroup record w DB
    3. Uruchom FocusGroupServiceLangChain.run_focus_group()
    4. Zwróć focus_group_id i status jako result
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Prowadzi focus group używając FocusGroupService.

        Args:
            node: Node config z {data: {config: {topics, participant_ids, ...}}}
            execution_context: Kontekst workflow (z persona_ids z poprzedniego node)

        Returns:
            {
                'focus_group_id': UUID,
                'participant_count': int,
                'questions': [...],
                'status': 'completed' | 'failed',
                'total_execution_time_ms': float (jeśli completed)
            }
        """
        # Parse config
        config_data = node.get('data', {}).get('config', {})
        config = RunFocusGroupNodeConfig(**config_data)

        project_id = execution_context['project_id']

        logger.info(
            f"Running focus group for project {project_id} "
            f"(workflow node {node['id']})"
        )

        # 1. Get participant_ids (z config lub z poprzedniego node output)
        participant_ids = self._get_participant_ids(config, execution_context)

        if not participant_ids:
            raise ValueError(
                "No participant_ids found for focus group. "
                "Either specify participant_ids in config or connect to a "
                "generate-personas node."
            )

        logger.info(f"Found {len(participant_ids)} participants for focus group")

        # 2. Validate personas exist
        await self._validate_personas(participant_ids, project_id)

        # 3. Generate questions z topics
        questions = self._generate_questions_from_topics(config.topics)

        logger.info(f"Generated {len(questions)} questions from topics")

        # 4. Create FocusGroup record w DB
        focus_group = FocusGroup(
            id=uuid4(),
            project_id=project_id,
            name=config.name or f"Focus Group - {node.get('data', {}).get('label', 'Unnamed')}",
            description=config.description or "Focus group created from workflow",
            persona_ids=[UUID(pid) if isinstance(pid, str) else pid for pid in participant_ids],
            questions=questions,
            status='pending',
        )

        self.db.add(focus_group)
        await self.db.commit()
        await self.db.refresh(focus_group)

        logger.info(f"Created FocusGroup {focus_group.id} in DB")

        # 5. Run focus group używając FocusGroupService
        fg_service = FocusGroupServiceLangChain()

        try:
            result = await fg_service.run_focus_group(
                db=self.db,
                focus_group_id=str(focus_group.id)
            )

            logger.info(
                f"Focus group {focus_group.id} completed: "
                f"status={result['status']}, "
                f"metrics={result.get('metrics')}"
            )

            # 6. Return result
            return {
                'focus_group_id': str(focus_group.id),
                'participant_count': len(participant_ids),
                'questions': questions,
                'status': result['status'],
                'total_execution_time_ms': result.get('metrics', {}).get(
                    'total_execution_time_ms'
                ),
            }

        except Exception as e:
            logger.error(
                f"Focus group {focus_group.id} failed: {e}",
                exc_info=True
            )

            # Update FocusGroup status to failed
            focus_group.status = 'failed'
            await self.db.commit()

            # Re-raise dla workflow executor
            raise

    def _get_participant_ids(
        self,
        config: RunFocusGroupNodeConfig,
        execution_context: dict[str, Any]
    ) -> list[str]:
        """Pobierz participant_ids z config lub poprzedniego node output.

        Priority:
        1. Config.participant_ids (jeśli podane)
        2. Poprzedni generate-personas node output (persona_ids)

        Args:
            config: Node config
            execution_context: Kontekst z results poprzednich nodes

        Returns:
            Lista persona IDs (UUIDs as strings)
        """
        # 1. Z config (jeśli podane)
        if config.participant_ids:
            return [str(pid) for pid in config.participant_ids]

        # 2. Z poprzedniego generate-personas node
        results = execution_context.get('results', {})

        for node_result in results.values():
            if 'persona_ids' in node_result:
                return node_result['persona_ids']

        # Not found
        return []

    async def _validate_personas(
        self,
        participant_ids: list[str],
        project_id: UUID
    ) -> None:
        """Sprawdź czy wszystkie personas istnieją w DB.

        Args:
            participant_ids: Lista persona IDs
            project_id: Project ID (dla validation)

        Raises:
            ValueError: Jeśli któraś persona nie istnieje
        """
        # Convert to UUIDs
        persona_uuids = [
            UUID(pid) if isinstance(pid, str) else pid
            for pid in participant_ids
        ]

        # Query DB
        stmt = select(Persona).where(
            Persona.id.in_(persona_uuids),
            Persona.project_id == project_id,
            Persona.is_active == True,  # noqa: E712
        )
        result = await self.db.execute(stmt)
        personas = result.scalars().all()

        # Check if all found
        found_ids = {str(p.id) for p in personas}
        missing = set(str(pid) for pid in persona_uuids) - found_ids

        if missing:
            raise ValueError(
                f"Personas not found or inactive: {', '.join(missing)}"
            )

    def _generate_questions_from_topics(
        self,
        topics: list[str]
    ) -> list[str]:
        """Generuj pytania focus group z topics.

        MVP: Proste mapowanie topics → questions (1:1).
        Future: Użyj LLM do generowania ciekawych pytań z topics.

        Args:
            topics: Lista topics (np. ["Product features", "Pricing"])

        Returns:
            Lista pytań dla focus group
        """
        if not topics:
            # Default questions jeśli brak topics
            return [
                "What are your thoughts on this topic?",
                "Can you share your experience with this?",
                "What would you improve?",
            ]

        # MVP: Simple mapping (topic → question)
        questions = []
        for topic in topics:
            # Basic question format
            question = f"What are your thoughts on {topic.lower()}?"
            questions.append(question)

        return questions
