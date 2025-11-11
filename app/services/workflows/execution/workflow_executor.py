"""Silnik wykonania workflow.

Ten moduł zawiera WorkflowExecutor - główny orchestrator wykonywania workflow.

Flow:
1. Validate workflow (pre-flight using WorkflowValidator)
2. Create WorkflowExecution record (tracking)
3. Topological sort nodes → execution order (Kahn's algorithm)
4. Execute nodes sekwencyjnie (MVP: no parallel execution)
5. Track progress (current_step_id, result_data)
6. Handle errors (mark failed, store error_message)

Performance target:
- Small workflow (3-5 nodes): <2 min
- Medium workflow (10-15 nodes): <10 min
- Large workflow (20+ nodes): <30 min
"""

import logging
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow, WorkflowExecution
from app.services.workflows.validation import WorkflowValidator
from app.services.workflows.nodes import (
    AnalyzeResultsExecutor,
    CreateSurveyExecutor,
    DecisionExecutor,
    EndExecutor,
    ExportPDFExecutor,
    GeneratePersonasExecutor,
    RunFocusGroupExecutor,
    StartExecutor,
)

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """Główny silnik wykonania workflow.

    Orchestruje wykonanie workflow:
    1. Validate workflow (pre-flight)
    2. Create WorkflowExecution record
    3. Topological sort nodes → execution order
    4. Execute nodes sekwencyjnie
    5. Track progress (current_step_id, result_data)
    6. Handle errors (mark failed, rollback?)

    Attributes:
        db: SQLAlchemy async session
        validator: WorkflowValidator instance
        node_executors: Registry node type → executor class
    """

    def __init__(self, db: AsyncSession):
        """Initialize executor.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.validator = WorkflowValidator()

        # Registry node type → executor class
        self.node_executors = {
            'start': StartExecutor,
            'end': EndExecutor,
            'generate-personas': GeneratePersonasExecutor,
            'run-focus-group': RunFocusGroupExecutor,
            'decision': DecisionExecutor,
            'create-survey': CreateSurveyExecutor,
            'analyze-results': AnalyzeResultsExecutor,
            'export-pdf': ExportPDFExecutor,
        }

    async def execute_workflow(
        self,
        workflow_id: UUID,
        user_id: UUID
    ) -> WorkflowExecution:
        """Główna metoda - wykonaj cały workflow.

        Args:
            workflow_id: UUID workflow do wykonania
            user_id: UUID użytkownika (dla auth + triggering)

        Returns:
            WorkflowExecution object z results

        Raises:
            ValueError: Jeśli validation fails
            Exception: Jeśli execution fails
        """
        logger.info(f"Starting execution of workflow {workflow_id}")

        # 1. Load workflow
        workflow = await self._load_workflow(workflow_id, user_id)

        logger.info(
            f"Loaded workflow '{workflow.name}' (project_id={workflow.project_id})"
        )

        # 2. Validate workflow (pre-flight)
        validation_result = await self.validator.validate_execution_readiness(
            workflow, self.db
        )

        if not validation_result.is_valid:
            errors = ', '.join(validation_result.errors)
            logger.error(f"Workflow validation failed: {errors}")
            raise ValueError(
                f"Workflow validation failed: {errors}"
            )

        logger.info("Workflow validation passed")

        # 3. Create execution record
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            triggered_by=user_id,
            status='pending',
            started_at=datetime.now(timezone.utc),
            result_data={}
        )
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)

        logger.info(f"Created WorkflowExecution {execution.id}")

        # 4. Topological sort → execution order
        nodes = workflow.canvas_data.get('nodes', [])
        edges = workflow.canvas_data.get('edges', [])

        execution_order = self._topological_sort(nodes, edges)

        logger.info(
            f"Execution order determined: {len(execution_order)} nodes "
            f"({', '.join(execution_order[:5])}{'...' if len(execution_order) > 5 else ''})"
        )

        # 5. Execute nodes sekwencyjnie
        execution.status = 'running'
        await self.db.commit()

        execution_context = {
            'project_id': workflow.project_id,
            'workflow_id': workflow_id,
            'user_id': user_id,
            'results': {}
        }

        try:
            nodes_map = {n['id']: n for n in nodes}

            for idx, node_id in enumerate(execution_order, 1):
                node = nodes_map[node_id]
                node_type = node.get('type')
                node_label = node.get('data', {}).get('label', node_id)

                logger.info(
                    f"[{idx}/{len(execution_order)}] Executing node "
                    f"'{node_label}' (id={node_id}, type={node_type})"
                )

                # Execute node
                result = await self._execute_node(node, execution_context)

                # Store result
                execution_context['results'][node_id] = result
                execution.result_data = execution_context['results']

                # Update execution record (dla progress tracking)
                # TODO: Map node_id → WorkflowStep.id if WorkflowStep exists
                await self.db.commit()

                logger.info(f"Node '{node_label}' completed successfully")

            # 6. Mark completed
            execution.status = 'completed'
            execution.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            logger.info(
                f"Workflow {workflow_id} completed successfully "
                f"({len(execution_order)} nodes executed)"
            )

        except Exception as e:
            # Handle error
            logger.error(
                f"Workflow {workflow_id} failed: {e}",
                exc_info=True
            )

            execution.status = 'failed'
            execution.error_message = str(e)[:1000]  # Truncate to 1000 chars
            execution.completed_at = datetime.now(timezone.utc)
            await self.db.commit()

            raise

        return execution

    async def _load_workflow(
        self,
        workflow_id: UUID,
        user_id: UUID
    ) -> Workflow:
        """Load workflow z auth check.

        Args:
            workflow_id: UUID workflow
            user_id: UUID użytkownika (dla auth)

        Returns:
            Workflow object

        Raises:
            ValueError: Jeśli workflow not found lub access denied
        """
        stmt = select(Workflow).where(
            and_(
                Workflow.id == workflow_id,
                Workflow.owner_id == user_id,
                Workflow.is_active == True,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError(
                f"Workflow {workflow_id} not found or access denied"
            )

        return workflow

    def _topological_sort(
        self,
        nodes: list[dict],
        edges: list[dict]
    ) -> list[str]:
        """Topological sort używając Kahn's algorithm.

        Zwraca nodes w execution order (DAG traversal).

        Args:
            nodes: Lista nodes z canvas [{id, type, data}, ...]
            edges: Lista edges z canvas [{source, target}, ...]

        Returns:
            Lista node IDs w execution order

        Raises:
            ValueError: Jeśli cycle detected (should not happen after validation)
        """
        # Build adjacency list + in-degree
        node_ids = [n['id'] for n in nodes]
        adj_list = defaultdict(list)
        in_degree = {nid: 0 for nid in node_ids}

        for edge in edges:
            source = edge['source']
            target = edge['target']
            adj_list[source].append(target)
            in_degree[target] += 1

        # Kahn's algorithm
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        sorted_nodes = []

        while queue:
            current = queue.popleft()
            sorted_nodes.append(current)

            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(node_ids):
            raise ValueError(
                "Cycle detected in workflow (should not happen after validation)"
            )

        return sorted_nodes

    async def _execute_node(
        self,
        node: dict,
        execution_context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute pojedynczy node.

        Args:
            node: Node z canvas {id, type, data: {label, config}}
            execution_context: Kontekst z previous results

        Returns:
            Result data z node execution

        Raises:
            NotImplementedError: Jeśli node type not implemented
            Exception: Jeśli node execution fails
        """
        node_type = node.get('type')
        node_id = node.get('id')
        node_label = node.get('data', {}).get('label', node_id)

        # Get executor dla tego typu
        executor_class = self.node_executors.get(node_type)

        if not executor_class:
            raise NotImplementedError(
                f"Node type '{node_type}' not implemented yet. "
                f"Node: '{node_label}' ({node_id})"
            )

        # Initialize executor i execute
        executor = executor_class(self.db)

        try:
            result = await executor.execute(node, execution_context)
            return result
        except Exception as e:
            logger.error(
                f"Node '{node_label}' ({node_id}, type={node_type}) failed: {e}",
                exc_info=True
            )
            raise
