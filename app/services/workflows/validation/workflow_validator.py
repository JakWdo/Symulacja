"""Serwis walidacji workflow.

Ten serwis przeprowadza pre-flight validation przed wykonaniem workflow:
1. Graph validation (DAG requirements, cycles, orphaned nodes)
2. Node config validation (required fields per type)
3. Dependency checks (external resources: project, personas, etc.)

Używany przed uruchomieniem workflow aby wykryć błędy konfiguracji.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque

from pydantic import ValidationError
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.schemas.workflow import (
    AnalyzeResultsNodeConfig,
    ConditionNodeConfig,
    CreateProjectNodeConfig,
    CreateSurveyNodeConfig,
    DecisionNodeConfig,
    EndNodeConfig,
    ExportPDFNodeConfig,
    GeneratePersonasNodeConfig,
    LoopNodeConfig,
    MergeNodeConfig,
    RunFocusGroupNodeConfig,
    StartNodeConfig,
    ValidationResult,
    WaitNodeConfig,
    WebhookNodeConfig,
)

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """Serwis walidacji workflow.

    Przeprowadza pre-flight validation przed wykonaniem workflow:
    1. Graph validation (DAG, cycles, orphaned nodes)
    2. Node config validation (required fields per type)
    3. Dependency checks (external resources)
    """

    # Map node type → Pydantic schema
    CONFIG_SCHEMAS = {
        "start": StartNodeConfig,
        "end": EndNodeConfig,
        "create-project": CreateProjectNodeConfig,
        "generate-personas": GeneratePersonasNodeConfig,
        "create-survey": CreateSurveyNodeConfig,
        "run-focus-group": RunFocusGroupNodeConfig,
        "analysis": AnalyzeResultsNodeConfig,
        "decision": DecisionNodeConfig,
        "wait": WaitNodeConfig,
        "export-pdf": ExportPDFNodeConfig,
        "webhook": WebhookNodeConfig,
        "condition": ConditionNodeConfig,
        "loop": LoopNodeConfig,
        "merge": MergeNodeConfig,
    }

    # Node types które są OUT OF SCOPE dla MVP
    MVP_DISABLED_TYPES = {"wait", "webhook", "condition", "loop"}

    async def validate_workflow_graph(self, workflow: Workflow) -> ValidationResult:
        """Waliduj graf workflow (DAG requirements).

        Sprawdza:
        1. Dokładnie jeden node typu 'start'
        2. Co najmniej jeden node typu 'end'
        3. Brak cykli (DAG using Kahn's algorithm)
        4. Brak orphaned nodes (wszystkie nodes reachable from start)
        5. Brak disconnected subgraphs

        Args:
            workflow: Workflow object z canvas_data

        Returns:
            ValidationResult z is_valid + errors list
        """
        logger.info(f"Validating workflow graph for workflow {workflow.id}")

        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        nodes = workflow.canvas_data.get("nodes", [])
        edges = workflow.canvas_data.get("edges", [])

        logger.debug(f"Found {len(nodes)} nodes, {len(edges)} edges")

        if not nodes:
            result.add_error("Workflow musi zawierać co najmniej jeden node")
            return result

        # 1. Sprawdź start node
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if len(start_nodes) == 0:
            result.add_error("Workflow musi mieć dokładnie jeden node typu 'start'")
        elif len(start_nodes) > 1:
            result.add_error(
                f"Workflow ma {len(start_nodes)} nodes typu 'start', wymagany jest dokładnie 1"
            )

        # 2. Sprawdź end nodes
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if len(end_nodes) == 0:
            result.add_error("Workflow musi mieć co najmniej jeden node typu 'end'")

        # 3. Wykryj cykle (Kahn's algorithm for topological sort)
        cycle_check = self._detect_cycles(nodes, edges)
        if cycle_check["has_cycle"]:
            cycle_path = " → ".join(cycle_check["cycle_path"])
            result.add_error(f"Workflow zawiera cykl: {cycle_path}")

        # 4. Wykryj orphaned nodes (nodes unreachable from start)
        if start_nodes and not cycle_check["has_cycle"]:
            start_id = start_nodes[0]["id"]
            reachable = self._get_reachable_nodes(start_id, nodes, edges)

            all_node_ids = {n["id"] for n in nodes}
            orphaned = all_node_ids - reachable

            if orphaned:
                orphaned_list = ", ".join(orphaned)
                result.add_error(
                    f"Orphaned nodes (niedostępne z start): {orphaned_list}"
                )

        # 5. Wykryj disconnected nodes (nodes z in-degree=0 i out-degree=0, poza start/end)
        disconnected = self._find_disconnected_nodes(nodes, edges)
        if disconnected:
            disconnected_list = ", ".join(disconnected)
            result.add_warning(
                f"Disconnected nodes (brak edges): {disconnected_list}"
            )

        logger.info(
            f"Graph validation completed: is_valid={result.is_valid}, "
            f"errors={len(result.errors)}, warnings={len(result.warnings)}"
        )

        return result

    def _detect_cycles(self, nodes: list[dict], edges: list[dict]) -> dict:
        """Wykryj cykle w grafie używając Kahn's algorithm.

        Kahn's algorithm:
        1. Zbuduj in-degree map (liczba incoming edges per node)
        2. Start z nodes o in-degree=0 (queue)
        3. Process nodes: usuń edges, zmniejsz in-degree targets
        4. Jeśli nie wszystkie nodes processed → cycle exists

        Args:
            nodes: Lista nodes [{id, type, data}, ...]
            edges: Lista edges [{source, target}, ...]

        Returns:
            {
                'has_cycle': bool,
                'cycle_path': list[str] (jeśli cycle znaleziony)
            }
        """
        # Build adjacency list i in-degree map
        node_ids = {n["id"] for n in nodes}
        adj_list = defaultdict(list)  # node_id -> [target_ids]
        in_degree = {nid: 0 for nid in node_ids}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]

            if source in node_ids and target in node_ids:
                adj_list[source].append(target)
                in_degree[target] += 1

        # Kahn's algorithm
        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        processed = []

        while queue:
            current = queue.popleft()
            processed.append(current)

            for neighbor in adj_list[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Jeśli nie wszystkie nodes processed → cycle
        if len(processed) != len(node_ids):
            # Find cycle path (dla error message)
            unprocessed = list(node_ids - set(processed))
            cycle_path = unprocessed[:3]  # Show first 3 nodes in cycle

            logger.warning(f"Cycle detected in workflow graph: {cycle_path}")

            return {"has_cycle": True, "cycle_path": cycle_path}

        return {"has_cycle": False, "cycle_path": []}

    def _get_reachable_nodes(
        self, start_id: str, nodes: list[dict], edges: list[dict]
    ) -> set[str]:
        """Znajdź wszystkie nodes reachable from start (BFS).

        Args:
            start_id: ID start node
            nodes: Lista wszystkich nodes
            edges: Lista edges

        Returns:
            Set of reachable node IDs
        """
        # Build adjacency list
        adj_list = defaultdict(list)
        for edge in edges:
            adj_list[edge["source"]].append(edge["target"])

        # BFS traversal
        visited = {start_id}
        queue = deque([start_id])

        while queue:
            current = queue.popleft()

            for neighbor in adj_list[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return visited

    def _find_disconnected_nodes(
        self, nodes: list[dict], edges: list[dict]
    ) -> list[str]:
        """Znajdź nodes bez żadnych edges (poza start/end).

        Args:
            nodes: Lista nodes
            edges: Lista edges

        Returns:
            Lista disconnected node IDs
        """
        # Count edges per node
        in_degree = defaultdict(int)
        out_degree = defaultdict(int)

        for edge in edges:
            out_degree[edge["source"]] += 1
            in_degree[edge["target"]] += 1

        # Find nodes z degree=0 (poza start/end które mogą mieć degree=0)
        disconnected = []
        for node in nodes:
            nid = node["id"]
            ntype = node.get("type")

            # Start ma out-degree=0 allowed, End ma in-degree=0 allowed
            if ntype in ["start", "end"]:
                continue

            if in_degree[nid] == 0 and out_degree[nid] == 0:
                disconnected.append(nid)

        return disconnected

    async def validate_node_configs(self, workflow: Workflow) -> ValidationResult:
        """Waliduj konfigurację każdego node.

        Sprawdza dla każdego node:
        1. Czy type jest jednym z 14 dozwolonych typów
        2. Czy node.data.config zawiera required fields per type
        3. Czy wartości są w dozwolonych zakresach

        Args:
            workflow: Workflow object z canvas_data

        Returns:
            ValidationResult z errors per node
        """
        logger.info(f"Validating node configs for workflow {workflow.id}")

        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        nodes = workflow.canvas_data.get("nodes", [])

        for node in nodes:
            node_id = node.get("id", "unknown")
            node_type = node.get("type")
            node_label = node.get("data", {}).get("label", node_id)

            # 1. Check if type is valid
            if node_type not in self.CONFIG_SCHEMAS:
                result.add_error(
                    f"Node '{node_label}' ({node_id}): Nieznany typ '{node_type}'"
                )
                continue

            # 2. MVP restrictions (disabled node types)
            if node_type in self.MVP_DISABLED_TYPES:
                result.add_warning(
                    f"Node '{node_label}' ({node_id}): Typ '{node_type}' "
                    f"jest OUT OF SCOPE dla MVP"
                )

            # 3. Validate config using Pydantic schema
            config_data = node.get("data", {}).get("config", {})
            schema = self.CONFIG_SCHEMAS[node_type]

            try:
                # Validate config
                schema(**config_data)
                logger.debug(
                    f"Node '{node_label}' ({node_id}) config validation passed"
                )
            except ValidationError as e:
                # Extract error messages
                for error in e.errors():
                    field = ".".join(str(x) for x in error["loc"])
                    message = error["msg"]
                    result.add_error(
                        f"Node '{node_label}' ({node_id}, typ: {node_type}): "
                        f"{field} - {message}"
                    )

        logger.info(
            f"Node config validation completed: is_valid={result.is_valid}, "
            f"errors={len(result.errors)}, warnings={len(result.warnings)}"
        )

        return result

    async def check_dependencies(
        self, workflow: Workflow, db: AsyncSession
    ) -> ValidationResult:
        """Sprawdź external dependencies (project, personas, etc.).

        Sprawdza:
        1. Project istnieje i jest active
        2. Dla 'run-focus-group' node: personas muszą istnieć (jeśli participant_ids podane)
        3. Dla 'create-survey' node z template_id: template istnieje

        Args:
            workflow: Workflow object
            db: Database session (async)

        Returns:
            ValidationResult z errors
        """
        logger.info(f"Checking dependencies for workflow {workflow.id}")

        result = ValidationResult(is_valid=True, errors=[], warnings=[])

        # Import models here to avoid circular imports
        from app.models import Persona, Project

        # 1. Sprawdź project
        project_stmt = select(Project).where(
            and_(
                Project.id == workflow.project_id,
                Project.is_active == True,  # noqa: E712
            )
        )
        project_result = await db.execute(project_stmt)
        project = project_result.scalar_one_or_none()

        if not project:
            result.add_error(
                f"Projekt {workflow.project_id} nie istnieje lub jest nieaktywny"
            )
            logger.warning(f"Project {workflow.project_id} not found or inactive")
            return result  # Critical error, stop checking

        # 2. Sprawdź node-specific dependencies
        nodes = workflow.canvas_data.get("nodes", [])

        for node in nodes:
            node_id = node.get("id", "unknown")
            node_type = node.get("type")
            node_label = node.get("data", {}).get("label", node_id)
            config = node.get("data", {}).get("config", {})

            # Focus group wymaga personas
            if node_type == "run-focus-group":
                participant_ids = config.get("participant_ids")

                if participant_ids:
                    # Sprawdź czy wszystkie personas istnieją
                    personas_stmt = select(Persona).where(
                        and_(
                            Persona.id.in_(participant_ids),
                            Persona.project_id == workflow.project_id,
                            Persona.is_active == True,  # noqa: E712
                        )
                    )
                    personas_result = await db.execute(personas_stmt)
                    personas = personas_result.scalars().all()

                    if len(personas) != len(participant_ids):
                        found_ids = {str(p.id) for p in personas}
                        missing = set(str(pid) for pid in participant_ids) - found_ids
                        missing_list = ", ".join(missing)
                        result.add_error(
                            f"Node '{node_label}' ({node_id}): "
                            f"Personas nie znalezione: {missing_list}"
                        )
                        logger.warning(
                            f"Missing personas for focus group node {node_id}: {missing}"
                        )

            # Survey template check (jeśli używamy templates w przyszłości)
            if node_type == "create-survey":
                template_id = config.get("template_id")
                if template_id:
                    # TODO: Validate template exists (gdy dodamy survey templates)
                    result.add_warning(
                        f"Node '{node_label}' ({node_id}): "
                        f"Walidacja survey template nie jest jeszcze zaimplementowana"
                    )
                    logger.debug(
                        f"Survey template validation not implemented for node {node_id}"
                    )

        logger.info(
            f"Dependency check completed: is_valid={result.is_valid}, "
            f"errors={len(result.errors)}, warnings={len(result.warnings)}"
        )

        return result

    async def validate_execution_readiness(
        self, workflow: Workflow, db: AsyncSession
    ) -> ValidationResult:
        """Combined validation - sprawdź czy workflow jest ready to execute.

        Łączy wszystkie 3 walidacje:
        1. Graph validation (DAG, cycles, orphaned nodes)
        2. Node config validation (required fields)
        3. Dependency checks (project, personas)

        Args:
            workflow: Workflow object
            db: Database session

        Returns:
            Aggregated ValidationResult
        """
        logger.info(
            f"Running combined validation for workflow {workflow.id} (name: {workflow.name})"
        )

        # Aggregate wszystkie validations
        graph_result = await self.validate_workflow_graph(workflow)
        config_result = await self.validate_node_configs(workflow)
        deps_result = await self.check_dependencies(workflow, db)

        # Merge results
        combined = ValidationResult(is_valid=True, errors=[], warnings=[])

        combined.errors.extend(graph_result.errors)
        combined.errors.extend(config_result.errors)
        combined.errors.extend(deps_result.errors)

        combined.warnings.extend(graph_result.warnings)
        combined.warnings.extend(config_result.warnings)
        combined.warnings.extend(deps_result.warnings)

        combined.is_valid = len(combined.errors) == 0

        logger.info(
            f"Combined validation completed for workflow {workflow.id}: "
            f"is_valid={combined.is_valid}, errors={len(combined.errors)}, "
            f"warnings={len(combined.warnings)}"
        )

        if not combined.is_valid:
            logger.warning(f"Workflow {workflow.id} validation failed with errors:")
            for error in combined.errors:
                logger.warning(f"  - {error}")

        return combined
