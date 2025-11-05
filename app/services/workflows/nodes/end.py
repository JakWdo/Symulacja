"""Executor dla node typu 'end'.

Node końcowy workflow - loguje zakończenie i markuje completion status.
"""

import logging
from typing import Any

from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class EndExecutor(NodeExecutor):
    """Executor dla node końcowego workflow.

    Node 'end' loguje zakończenie workflow i markuje status completion.
    Może być wiele nodes typu 'end' w workflow (dla różnych ścieżek).
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Wykonaj node końcowy (mark completion).

        Args:
            node: Node config z canvas
            execution_context: Kontekst workflow

        Returns:
            {
                'node_type': 'end',
                'status': 'completed',
                'workflow_id': UUID,
                'total_nodes_executed': int
            }
        """
        workflow_id = execution_context['workflow_id']
        results = execution_context.get('results', {})
        total_nodes = len(results)

        logger.info(
            f"Workflow {workflow_id} reached end node. "
            f"Total nodes executed: {total_nodes}"
        )

        return {
            'node_type': 'end',
            'status': 'completed',
            'workflow_id': str(workflow_id),
            'total_nodes_executed': total_nodes
        }
