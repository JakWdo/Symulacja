"""Executor dla node typu 'create-survey'.

STUB - Out of scope dla MVP.
"""

import logging
from typing import Any

from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class CreateSurveyExecutor(NodeExecutor):
    """Executor dla tworzenia survey.

    MVP: OUT OF SCOPE - Not implemented yet.
    Future: Integrate z SurveyService.
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Placeholder - survey creation not implemented.

        Raises:
            NotImplementedError: MVP feature not implemented
        """
        logger.warning(
            "create-survey node executed, but feature is OUT OF SCOPE for MVP"
        )

        raise NotImplementedError(
            "Survey creation is OUT OF SCOPE for MVP. "
            "Please remove 'create-survey' nodes from workflow or wait for v1.1 release."
        )
