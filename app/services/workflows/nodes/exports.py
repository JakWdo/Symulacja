"""Executor dla node typu 'export-pdf'.

STUB - Out of scope dla MVP.
"""

import logging
from typing import Any

from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class ExportPDFExecutor(NodeExecutor):
    """Executor dla eksportu do PDF.

    MVP: OUT OF SCOPE - Not implemented yet.
    Future: Generate PDF reports z workflow results.
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Placeholder - PDF export not implemented.

        Raises:
            NotImplementedError: MVP feature not implemented
        """
        logger.warning(
            "export-pdf node executed, but feature is OUT OF SCOPE for MVP"
        )

        raise NotImplementedError(
            "PDF export is OUT OF SCOPE for MVP. "
            "Please remove 'export-pdf' nodes from workflow or wait for v1.1 release."
        )
