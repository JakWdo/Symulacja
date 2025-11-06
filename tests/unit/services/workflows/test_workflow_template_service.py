"""
Tests dla WorkflowTemplateService - zarządzanie workflow templates.

Coverage:
- Template retrieval (get all, get by ID)
- Template validation (wszystkie 6 templates są valid DAGs)
- Template instantiation (tworzenie workflow z template)
- Edge cases (invalid template_id, null project_id, etc.)

Target coverage: 85%+ dla workflow_template_service.py
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import Workflow
from app.services.workflows.workflow_template_service import WorkflowTemplateService
from app.services.workflows.workflow_validator import WorkflowValidator


# ==================== TEMPLATE RETRIEVAL TESTS ====================


def test_get_all_templates():
    """Test pobierania wszystkich 6 templates."""
    service = WorkflowTemplateService()

    templates = service.get_templates()

    # Sprawdź liczbę templates
    assert len(templates) == 6

    # Sprawdź podstawową strukturę
    assert all(hasattr(t, "id") for t in templates)
    assert all(hasattr(t, "name") for t in templates)
    assert all(hasattr(t, "description") for t in templates)
    assert all(hasattr(t, "canvas_data") for t in templates)
    assert all(hasattr(t, "tags") for t in templates)
    assert all(hasattr(t, "node_count") for t in templates)
    assert all(hasattr(t, "estimated_time_minutes") for t in templates)


def test_get_all_templates_has_correct_ids():
    """Test że wszystkie oczekiwane template IDs są obecne."""
    service = WorkflowTemplateService()

    templates = service.get_templates()
    template_ids = [t.id for t in templates]

    expected_ids = [
        "basic_research",
        "deep_dive",
        "iterative_validation",
        "brand_perception",
        "user_journey",
        "feature_prioritization",
    ]

    assert set(template_ids) == set(expected_ids)


def test_templates_have_metadata():
    """Test że templates zawierają pełne metadata."""
    service = WorkflowTemplateService()

    templates = service.get_templates()

    for template in templates:
        # Tags
        assert hasattr(template, "tags")
        assert isinstance(template.tags, list)
        assert len(template.tags) > 0  # Każdy template powinien mieć jakieś tagi

        # Estimated time
        assert hasattr(template, "estimated_time_minutes")
        assert isinstance(template.estimated_time_minutes, int)
        assert template.estimated_time_minutes > 0

        # Node count
        assert hasattr(template, "node_count")
        assert isinstance(template.node_count, int)
        assert template.node_count > 0

        # Category
        assert hasattr(template, "category")
        assert template.category in ["research", "validation", "optimization"]


def test_templates_sorted_by_estimated_time():
    """Test że templates są posortowane po estimated_time_minutes."""
    service = WorkflowTemplateService()

    templates = service.get_templates()

    # Sprawdź czy są posortowane rosnąco
    times = [t.estimated_time_minutes for t in templates]
    assert times == sorted(times)


# ==================== GET TEMPLATE BY ID TESTS ====================


def test_get_template_by_id_exists():
    """Test pobierania istniejącego template po ID."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("basic_research")

    assert template is not None
    assert template.id == "basic_research"
    assert template.name == "Basic Research"
    assert "canvas_data" in template.model_dump()
    assert hasattr(template.canvas_data, 'nodes')
    assert hasattr(template.canvas_data, 'edges')


def test_get_template_by_id_not_found():
    """Test że zwraca None gdy template nie istnieje."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("nonexistent_template")

    assert template is None


def test_get_all_templates_by_id():
    """Test pobierania każdego template po ID działa."""
    service = WorkflowTemplateService()

    template_ids = [
        "basic_research",
        "deep_dive",
        "iterative_validation",
        "brand_perception",
        "user_journey",
        "feature_prioritization",
    ]

    for template_id in template_ids:
        template = service.get_template_by_id(template_id)
        assert template is not None
        assert template.id == template_id


# ==================== TEMPLATE STRUCTURE TESTS ====================


def test_basic_research_template_structure():
    """Test struktury basic_research template."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("basic_research")
    nodes = template.canvas_data.nodes
    edges = template.canvas_data.edges

    # Powinien mieć 5 nodes: start, personas, survey, analysis, end
    assert len(nodes) == 5

    node_types = [n.type for n in nodes]
    assert "start" in node_types
    assert "generate-personas" in node_types
    assert "create-survey" in node_types
    assert "analyze-results" in node_types
    assert "end" in node_types

    # Powinien mieć 4 edges (linear flow)
    assert len(edges) == 4


def test_deep_dive_template_structure():
    """Test struktury deep_dive template."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("deep_dive")
    nodes = template.canvas_data.nodes

    # Powinien mieć 6 nodes
    assert len(nodes) == 6

    node_types = [n.type for n in nodes]
    assert "start" in node_types
    assert "generate-personas" in node_types
    assert "create-survey" in node_types
    assert "run-focus-group" in node_types
    assert "analyze-results" in node_types
    assert "end" in node_types


def test_iterative_validation_template_structure():
    """Test struktury iterative_validation template."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("iterative_validation")
    nodes = template.canvas_data.nodes

    # Powinien mieć 5 nodes: start, personas, focus-group, decision, end
    assert len(nodes) == 5

    node_types = [n.type for n in nodes]
    assert "start" in node_types
    assert "generate-personas" in node_types
    assert "run-focus-group" in node_types
    assert "decision" in node_types
    assert "end" in node_types


def test_brand_perception_template_structure():
    """Test struktury brand_perception template."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("brand_perception")
    nodes = template.canvas_data.nodes

    # Powinien mieć 5 nodes
    assert len(nodes) == 5

    node_types = [n.type for n in nodes]
    assert "start" in node_types
    assert "generate-personas" in node_types
    assert "create-survey" in node_types
    assert "analyze-results" in node_types
    assert "end" in node_types


def test_user_journey_template_structure():
    """Test struktury user_journey template."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("user_journey")
    nodes = template.canvas_data.nodes

    # Powinien mieć 6 nodes
    assert len(nodes) == 6

    node_types = [n.type for n in nodes]
    assert "start" in node_types
    assert "generate-personas" in node_types
    assert "run-focus-group" in node_types
    assert "analyze-results" in node_types
    assert "export-pdf" in node_types
    assert "end" in node_types


def test_feature_prioritization_template_structure():
    """Test struktury feature_prioritization template."""
    service = WorkflowTemplateService()

    template = service.get_template_by_id("feature_prioritization")
    nodes = template.canvas_data.nodes

    # Powinien mieć 6 nodes
    assert len(nodes) == 6

    node_types = [n.type for n in nodes]
    assert "start" in node_types
    assert "generate-personas" in node_types
    assert "create-survey" in node_types
    assert "analyze-results" in node_types
    assert "decision" in node_types
    assert "end" in node_types


# ==================== TEMPLATE VALIDATION TESTS ====================


def test_validate_all_templates_are_valid_dags():
    """Test że wszystkie 6 templates są valid DAGs."""
    service = WorkflowTemplateService()
    validator = WorkflowValidator()  # No arguments needed

    templates = service.get_templates()

    for template in templates:
        nodes = template.canvas_data.nodes
        edges = template.canvas_data.edges

        # Sprawdź start node
        start_nodes = [n for n in nodes if n.type == "start"]
        assert len(start_nodes) >= 1, f"Template {template.id} brakuje START node"

        # Sprawdź end node
        end_nodes = [n for n in nodes if n.type == "end"]
        assert len(end_nodes) >= 1, f"Template {template.id} brakuje END node"

        # Konwertuj do dict dla validatora (validator oczekuje dict)
        nodes_dict = [n.model_dump() for n in nodes]
        edges_dict = [e.model_dump() for e in edges]

        # Sprawdź brak cykli (Kahn's algorithm)
        cycle_check = validator._detect_cycles(nodes_dict, edges_dict)
        assert not cycle_check["has_cycle"], f"Template {template.id} zawiera cykl: {cycle_check['cycle_path']}"

        # Sprawdź brak orphaned nodes
        start_id = start_nodes[0].id
        reachable = validator._get_reachable_nodes(start_id, nodes_dict, edges_dict)
        all_node_ids = {n.id for n in nodes}

        orphaned = all_node_ids - reachable
        assert len(orphaned) == 0, f"Template {template.id} ma orphaned nodes: {orphaned}"


def test_validate_template_method_basic_research():
    """Test validate_template() dla basic_research."""
    service = WorkflowTemplateService()

    is_valid, errors = service.validate_template("basic_research")

    assert is_valid is True
    assert len(errors) == 0


def test_validate_template_method_all_templates():
    """Test validate_template() dla wszystkich 6 templates."""
    service = WorkflowTemplateService()

    template_ids = [
        "basic_research",
        "deep_dive",
        "iterative_validation",
        "brand_perception",
        "user_journey",
        "feature_prioritization",
    ]

    for template_id in template_ids:
        is_valid, errors = service.validate_template(template_id)
        assert is_valid is True, f"Template {template_id} validation failed: {errors}"
        assert len(errors) == 0


def test_validate_template_invalid_id():
    """Test validate_template() dla nieistniejącego template."""
    service = WorkflowTemplateService()

    is_valid, errors = service.validate_template("nonexistent")

    assert is_valid is False
    assert len(errors) > 0
    assert any("not found" in err for err in errors)


def test_validate_all_templates_method():
    """Test validate_all_templates() zwraca results dla wszystkich."""
    service = WorkflowTemplateService()

    results = service.validate_all_templates()

    assert len(results) == 6
    assert all(template_id in results for template_id in service.TEMPLATES.keys())

    # Wszystkie powinny być valid
    for template_id, (is_valid, errors) in results.items():
        assert is_valid is True, f"Template {template_id} jest invalid: {errors}"
        assert len(errors) == 0


# ==================== TEMPLATE NODE COUNT TESTS ====================


def test_template_node_counts_accurate():
    """Test że node_count metadata odpowiada rzeczywistej liczbie nodes."""
    service = WorkflowTemplateService()

    templates = service.get_templates()

    for template in templates:
        actual_count = len(template.canvas_data.nodes)
        metadata_count = template.node_count

        assert actual_count == metadata_count, (
            f"Template {template.id}: node_count={metadata_count} "
            f"ale ma {actual_count} nodes"
        )


# ==================== TEMPLATE INSTANTIATION TESTS ====================


@pytest.mark.asyncio
async def test_instantiate_template_success(db_session: AsyncSession, test_user, test_project):
    """Test tworzenia workflow z template."""
    service = WorkflowTemplateService()

    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="My Research Workflow",
        db=db_session,
    )

    assert workflow.id is not None
    assert workflow.name == "My Research Workflow"
    assert workflow.project_id == test_project.id
    assert workflow.owner_id == test_user.id
    assert workflow.is_template is False
    assert workflow.status == "draft"

    # Verify canvas_data skopiowany z template
    assert "nodes" in workflow.canvas_data
    assert "edges" in workflow.canvas_data
    assert len(workflow.canvas_data.nodes) == 5  # basic_research ma 5 nodes


@pytest.mark.asyncio
async def test_instantiate_template_auto_generated_name(db_session: AsyncSession, test_user, test_project):
    """Test że nazwa workflow jest auto-generowana jeśli nie podano."""
    service = WorkflowTemplateService()

    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name=None,  # Auto-generate
        db=db_session,
    )

    assert workflow.name is not None
    assert "Basic Research" in workflow.name
    assert "template" in workflow.name.lower()


@pytest.mark.asyncio
async def test_instantiate_template_invalid_template_id(db_session: AsyncSession, test_user, test_project):
    """Test ValueError gdy template nie istnieje."""
    service = WorkflowTemplateService()

    with pytest.raises(ValueError) as exc_info:
        await service.create_from_template(
            template_id="nonexistent",
            project_id=test_project.id,
            user_id=test_user.id,
            workflow_name="Test",
            db=db_session,
        )

    assert "not found" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_instantiate_all_templates(db_session: AsyncSession, test_user, test_project):
    """Test instantiation dla każdego z 6 templates działa."""
    service = WorkflowTemplateService()

    template_ids = [
        "basic_research",
        "deep_dive",
        "iterative_validation",
        "brand_perception",
        "user_journey",
        "feature_prioritization",
    ]

    for template_id in template_ids:
        workflow = await service.create_from_template(
            template_id=template_id,
            project_id=test_project.id,
            user_id=test_user.id,
            workflow_name=f"Test {template_id}",
            db=db_session,
        )

        assert workflow is not None
        assert workflow.project_id == test_project.id
        assert workflow.name == f"Test {template_id}"
        assert len(workflow.canvas_data.nodes) > 0


@pytest.mark.asyncio
async def test_instantiate_template_creates_db_record(db_session: AsyncSession, test_user, test_project):
    """Test że workflow jest zapisany w bazie danych."""
    service = WorkflowTemplateService()

    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="DB Test Workflow",
        db=db_session,
    )

    # Verify w DB
    stmt = select(Workflow).where(Workflow.id == workflow.id)
    result = await db_session.execute(stmt)
    db_workflow = result.scalar_one()

    assert db_workflow is not None
    assert db_workflow.name == "DB Test Workflow"
    assert db_workflow.canvas_data == workflow.canvas_data
    assert db_workflow.project_id == test_project.id
    assert db_workflow.owner_id == test_user.id


@pytest.mark.asyncio
async def test_instantiate_template_canvas_data_deep_copy(db_session: AsyncSession, test_user, test_project):
    """Test że canvas_data jest deep copy (modyfikacja nie wpływa na template)."""
    service = WorkflowTemplateService()

    # Pobierz template przed instantiation
    template_before = service.get_template_by_id("basic_research")
    original_canvas = template_before.canvas_data.copy()

    # Utwórz workflow
    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="Deep Copy Test",
        db=db_session,
    )

    # Zmodyfikuj canvas_data w workflow
    workflow.canvas_data.nodes[0]["data"]["label"] = "MODIFIED"
    await db_session.commit()

    # Sprawdź że template nie został zmodyfikowany
    template_after = service.get_template_by_id("basic_research")
    assert template_after.canvas_data == original_canvas


# ==================== EDGE CASES TESTS ====================


@pytest.mark.asyncio
async def test_instantiate_template_long_workflow_name(db_session: AsyncSession, test_user, test_project):
    """Test instantiation z bardzo długą nazwą workflow."""
    service = WorkflowTemplateService()
    long_name = "A" * 255  # Max length dla name column

    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name=long_name,
        db=db_session,
    )

    assert workflow.name == long_name
    assert len(workflow.name) == 255


@pytest.mark.asyncio
async def test_instantiate_multiple_from_same_template(db_session: AsyncSession, test_user, test_project):
    """Test tworzenia wielu workflows z tego samego template."""
    service = WorkflowTemplateService()

    workflow1 = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="Instance 1",
        db=db_session,
    )

    workflow2 = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="Instance 2",
        db=db_session,
    )

    assert workflow1.id != workflow2.id
    assert workflow1.name != workflow2.name
    # Oba powinny mieć identyczny canvas_data (ale różne objects)
    assert workflow1.canvas_data == workflow2.canvas_data
    assert workflow1.canvas_data is not workflow2.canvas_data


@pytest.mark.asyncio
async def test_instantiate_template_preserves_node_configs(db_session: AsyncSession, test_user, test_project):
    """Test że node configs z template są zachowane w workflow."""
    service = WorkflowTemplateService()

    # Pobierz template
    template = service.get_template_by_id("basic_research")
    template_persona_node = next(n for n in template.canvas_data.nodes if n.type == "generate-personas")
    template_config = template_persona_node["data"]["config"]

    # Utwórz workflow
    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="Config Test",
        db=db_session,
    )

    # Sprawdź że config został skopiowany
    workflow_persona_node = next(n for n in workflow.canvas_data.nodes if n.type == "generate-personas")
    workflow_config = workflow_persona_node["data"]["config"]

    assert workflow_config == template_config
    assert "count" in workflow_config
    assert "demographic_preset" in workflow_config


@pytest.mark.asyncio
async def test_instantiate_template_empty_description(db_session: AsyncSession, test_user, test_project):
    """Test instantiation gdy description nie jest podany."""
    service = WorkflowTemplateService()

    workflow = await service.create_from_template(
        template_id="basic_research",
        project_id=test_project.id,
        user_id=test_user.id,
        workflow_name="No Description Test",
        db=db_session,
    )

    # Description powinien być wzięty z template
    template = service.get_template_by_id("basic_research")
    assert workflow.description == template.description


# ==================== TEMPLATE CATEGORIES TESTS ====================


def test_templates_have_valid_categories():
    """Test że wszystkie templates mają valid category."""
    service = WorkflowTemplateService()

    templates = service.get_templates()
    valid_categories = ["research", "validation", "optimization"]

    for template in templates:
        assert template.category in valid_categories


def test_templates_grouped_by_category():
    """Test że można pogrupować templates po category."""
    service = WorkflowTemplateService()

    templates = service.get_templates()

    # Grupuj po category
    by_category = {}
    for template in templates:
        category = template.category
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(template)

    # Sprawdź że są templates w każdej kategorii
    assert len(by_category) > 0
    assert all(len(templates) > 0 for templates in by_category.values())


# ==================== TEMPLATE TAGS TESTS ====================


def test_templates_have_relevant_tags():
    """Test że templates mają odpowiednie tagi."""
    service = WorkflowTemplateService()

    # Basic research powinien mieć tag "beginner"
    basic = service.get_template_by_id("basic_research")
    assert "beginner" in basic.tags or "quick" in basic.tags

    # Deep dive powinien mieć tag "advanced"
    deep = service.get_template_by_id("deep_dive")
    assert "advanced" in deep.tags or "focus-group" in deep.tags

    # User journey powinien mieć tag "ux"
    journey = service.get_template_by_id("user_journey")
    assert "ux" in journey.tags or "journey" in journey.tags


def test_templates_can_be_filtered_by_tags():
    """Test że można filtrować templates po tagach."""
    service = WorkflowTemplateService()

    templates = service.get_templates()

    # Znajdź templates z tagiem "personas"
    persona_templates = [t for t in templates if "personas" in t.tags]

    # Wszystkie templates powinny mieć personas (bo wszystkie generują personas)
    assert len(persona_templates) > 0

    # Znajdź templates z tagiem "survey"
    survey_templates = [t for t in templates if "survey" in t.tags]
    assert len(survey_templates) > 0
