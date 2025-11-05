"""Executor dla node typu 'decision'.

Conditional branching w workflow - ewaluacja condition i wybór ścieżki.
"""

import logging
from typing import Any

from app.schemas.workflow import DecisionNodeConfig
from app.services.workflows.nodes.base import NodeExecutor

logger = logging.getLogger(__name__)


class DecisionExecutor(NodeExecutor):
    """Executor dla conditional branching w workflow.

    Ewaluuje condition (Python expression) i wybiera branch (true/false).
    Używa restricted eval dla bezpieczeństwa.

    WAŻNE: Safe eval - tylko allowlisted funkcje i zmienne z execution context.
    """

    async def execute(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Ewaluuje condition i wybiera branch.

        Args:
            node: Node config z {data: {config: {condition}}}
            execution_context: Kontekst z previous results

        Returns:
            {
                'condition': str,
                'result': bool,
                'branch_taken': 'true' | 'false',
                'evaluation_context': dict (zmienne użyte w eval)
            }
        """
        # Parse config
        config_data = node.get('data', {}).get('config', {})
        config = DecisionNodeConfig(**config_data)

        condition = config.condition or 'True'

        logger.info(f"Evaluating decision: {condition}")

        # 1. Build safe evaluation context z previous results
        eval_context = self._build_eval_context(execution_context)

        logger.debug(f"Evaluation context: {eval_context}")

        # 2. Safe eval (restricted builtins)
        try:
            result = self._safe_eval(condition, eval_context)
            result_bool = bool(result)
        except Exception as e:
            logger.error(f"Decision eval failed: {e}")
            raise ValueError(
                f"Invalid condition: {condition}. Error: {str(e)}"
            ) from e

        # 3. Determine branch
        branch = 'true' if result_bool else 'false'

        logger.info(f"Decision result: {result_bool} → {branch} branch")

        return {
            'condition': condition,
            'result': result_bool,
            'branch_taken': branch,
            'evaluation_context': eval_context,
        }

    def _build_eval_context(
        self,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Build safe evaluation context z execution_context.

        Ekstraktuje użyteczne zmienne z previous node results dla użycia w condition.

        Args:
            execution_context: Kontekst workflow z results

        Returns:
            Dict ze zmiennymi dla eval (np. {'persona_count': 20, 'personas': [...]})
        """
        eval_context = {}

        # Extract results z poprzednich nodes
        results = execution_context.get('results', {})

        # Extract common variables
        for node_id, node_result in results.items():
            # Persona generation results
            if 'persona_ids' in node_result:
                eval_context['personas'] = node_result['persona_ids']
                eval_context['persona_count'] = len(node_result['persona_ids'])

            # Focus group results
            if 'focus_group_id' in node_result:
                eval_context['focus_group_id'] = node_result['focus_group_id']
                eval_context['focus_group_status'] = node_result.get('status')

            # Survey results
            if 'survey_id' in node_result:
                eval_context['survey_id'] = node_result['survey_id']
                eval_context['survey_response_count'] = node_result.get(
                    'response_count', 0
                )

        # Add safe builtins
        eval_context['len'] = len
        eval_context['str'] = str
        eval_context['int'] = int
        eval_context['float'] = float
        eval_context['bool'] = bool

        # Add constants
        eval_context['True'] = True
        eval_context['False'] = False
        eval_context['None'] = None

        return eval_context

    def _safe_eval(
        self,
        condition: str,
        eval_context: dict[str, Any]
    ) -> Any:
        """Safe eval z restricted builtins.

        UWAGA: Używa eval() z __builtins__={} dla bezpieczeństwa.
        Tylko zmienne z eval_context są dostępne.

        Args:
            condition: Python expression do eval
            eval_context: Dict ze zmiennymi i funkcjami

        Returns:
            Result expression eval

        Raises:
            Exception: Jeśli eval fails (syntax error, undefined variable, etc.)
        """
        # Restricted eval - tylko eval_context variables
        # __builtins__={} blokuje dostęp do __import__, exec, open, etc.
        try:
            result = eval(
                condition,
                {"__builtins__": {}},  # No builtins (bezpieczeństwo!)
                eval_context
            )
            return result
        except Exception as e:
            logger.error(
                f"Safe eval failed for condition '{condition}': {e}",
                exc_info=True
            )
            raise
