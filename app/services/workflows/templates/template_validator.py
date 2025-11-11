"""
Moduł Walidacji Workflow Templates

Odpowiedzialny za:
- Walidację struktury templates (start node, end node, valid edges)
- Sprawdzanie kompletności nodes i edges
- Weryfikację spójności referencji między nodes i edges
"""

import logging

logger = logging.getLogger(__name__)


class WorkflowTemplateValidator:
    """
    Walidacja workflow templates

    Sprawdza poprawność struktury templates, aby zapewnić że:
    - Template ma start node i end node
    - Edges wskazują na istniejące nodes
    - Template ma przynajmniej jeden node
    """

    @staticmethod
    def validate_template(template_id: str, template_data: dict) -> tuple[bool, list[str]]:
        """
        Waliduje template structure (start node, end node, valid edges)

        Args:
            template_id: ID template do walidacji
            template_data: Dict z danymi template

        Returns:
            Tuple (is_valid, errors)
            - is_valid: True jeśli template jest poprawny
            - errors: Lista błędów walidacji (pusta jeśli poprawny)
        """
        if not template_data:
            return False, [f"Template '{template_id}' not found"]

        errors = []
        canvas_data = template_data.get("canvas_data", {})
        nodes = canvas_data.get("nodes", [])
        edges = canvas_data.get("edges", [])

        # Sprawdź czy są nodes
        if not nodes:
            errors.append("Template must have at least one node")

        # Sprawdź start node
        start_nodes = [n for n in nodes if n.get("type") == "start"]
        if len(start_nodes) == 0:
            errors.append("Template must have at least one 'start' node")
        elif len(start_nodes) > 1:
            errors.append("Template should have only one 'start' node")

        # Sprawdź end node
        end_nodes = [n for n in nodes if n.get("type") == "end"]
        if len(end_nodes) == 0:
            errors.append("Template must have at least one 'end' node")

        # Sprawdź edges - czy source/target istnieją
        node_ids = {n.get("id") for n in nodes if n.get("id")}
        for edge in edges:
            edge_id = edge.get("id", "unknown")
            source = edge.get("source")
            target = edge.get("target")

            if source and source not in node_ids:
                errors.append(
                    f"Edge '{edge_id}' references non-existent source node '{source}'"
                )
            if target and target not in node_ids:
                errors.append(
                    f"Edge '{edge_id}' references non-existent target node '{target}'"
                )

        is_valid = len(errors) == 0

        if is_valid:
            logger.debug(f"Template '{template_id}' validation passed")
        else:
            logger.warning(f"Template '{template_id}' validation failed: {errors}")

        return is_valid, errors

    @staticmethod
    def validate_all_templates(templates_dict: dict) -> dict[str, tuple[bool, list[str]]]:
        """
        Waliduje wszystkie templates

        Args:
            templates_dict: Dict zawierający wszystkie templates {template_id: template_data}

        Returns:
            Dict {template_id: (is_valid, errors)}
        """
        results = {}

        for template_id, template_data in templates_dict.items():
            is_valid, errors = WorkflowTemplateValidator.validate_template(
                template_id, template_data
            )
            results[template_id] = (is_valid, errors)

        logger.info(f"Validated {len(results)} templates")
        return results
