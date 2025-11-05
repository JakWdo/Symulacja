"""Executor dla node typu 'start'.

Node startowy workflow - nie wykonuje żadnej operacji, tylko loguje początek wykonania.
"""

import logging
from typing import Any

from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class StartExecutor(NodeExecutor):
    """Executor dla node startowego workflow.

    Node 'start' nie wykonuje żadnych operacji biznesowych, służy tylko
    jako punkt wejścia do workflow i loguje rozpoczęcie wykonania.
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Wykonaj node startowy (no-op z logowaniem).

        Args:
            node: Node config z canvas
            execution_context: Kontekst workflow

        Returns:
            {
                'node_type': 'start',
                'status': 'initialized',
                'workflow_id': UUID,
                'project_id': UUID
            }
        """
        workflow_id = execution_context['workflow_id']
        project_id = execution_context['project_id']

        logger.info(
            f"Workflow {workflow_id} started for project {project_id}"
        )

        return {
            'node_type': 'start',
            'status': 'initialized',
            'workflow_id': str(workflow_id),
            'project_id': str(project_id)
        }
