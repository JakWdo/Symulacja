"""Executor dla node typu 'analyze-results'.

STUB - Out of scope dla MVP.
"""

import logging
from typing import Any

from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class AnalyzeResultsExecutor(NodeExecutor):
    """Executor dla analizy results.

    MVP: OUT OF SCOPE - Not implemented yet.
    Future: Integrate z LLM-based analysis (insights extraction, sentiment, themes).
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Placeholder - results analysis not implemented.

        Raises:
            NotImplementedError: MVP feature not implemented
        """
        logger.warning(
            "analyze-results node executed, but feature is OUT OF SCOPE for MVP"
        )

        raise NotImplementedError(
            "Results analysis is OUT OF SCOPE for MVP. "
            "Please remove 'analyze-results' nodes from workflow or wait for v1.1 release."
        )
