"""Base class dla node executors.

Ten moduł definiuje abstrakcyjną klasę bazową dla wszystkich executorów węzłów workflow.
Każdy typ węzła (generate-personas, run-focus-group, etc.) dziedziczy z NodeExecutor
i implementuje swoją logikę wykonania.

Pattern: Strategy Pattern - każdy node type ma swoją strategię wykonania.
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class NodeExecutor(ABC):
    """Bazowa klasa dla executorów węzłów workflow.

    Każdy typ węzła (generate-personas, run-focus-group, etc.) dziedziczy z tej klasy
    i implementuje metodę execute().

    Pattern: Strategy Pattern - każdy node type ma swoją strategię wykonania.

    Attributes:
        db: SQLAlchemy async session do operacji bazodanowych
    """

    def __init__(self, db: AsyncSession):
        """Initialize executor z database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    @abstractmethod
    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Wykonaj node i zwróć results.

        Metoda abstrakcyjna która musi być zaimplementowana przez każdy konkretny executor.

        Args:
            node: Node z React Flow {
                'id': str,
                'type': str,
                'data': {
                    'label': str,
                    'config': dict  # Konfiguracja specyficzna dla typu węzła
                }
            }
            execution_context: Kontekst z poprzednich nodes {
                'project_id': UUID,
                'workflow_id': UUID,
                'user_id': UUID,
                'results': {node_id: {result_data}}  # Wyniki poprzednich węzłów
            }

        Returns:
            Result data dla tego node (stored w execution.result_data).
            Format zależy od typu węzła, ale zawsze dict[str, Any].

        Raises:
            Exception: Jeśli execution fails (error message powinien być czytelny dla usera)
        """
        pass
