# WorkflowValidator - Test Cases Draft

Ten plik zawiera draft unit test cases dla `tests/unit/services/workflows/test_workflow_validator.py`.

## Test File Structure

```python
"""Unit tests dla WorkflowValidator.

Testuje pre-flight validation workflow:
1. Graph structure validation (DAG, cycles, orphaned nodes)
2. Node config validation (required fields, value ranges)
3. Dependency checks (project, personas)
"""

import pytest
from uuid import uuid4
from app.services.workflows import WorkflowValidator
from app.models.workflow import Workflow
from app.schemas.workflow import ValidationResult


# ==================== FIXTURES ====================

@pytest.fixture
def validator():
    """Fixture: WorkflowValidator instance."""
    return WorkflowValidator()


@pytest.fixture
def valid_workflow_data():
    """Fixture: Valid workflow canvas data."""
    return {
        "nodes": [
            {
                "id": "node-start",
                "type": "start",
                "data": {
                    "label": "Start",
                    "config": {"trigger_type": "manual"}
                }
            },
            {
                "id": "node-personas",
                "type": "generate-personas",
                "data": {
                    "label": "Generate Personas",
                    "config": {
                        "count": 20,
                        "demographic_preset": "millennials",
                        "target_audience_description": "Tech-savvy professionals"
                    }
                }
            },
            {
                "id": "node-end",
                "type": "end",
                "data": {
                    "label": "End",
                    "config": {"success_message": "Workflow completed"}
                }
            }
        ],
        "edges": [
            {"source": "node-start", "target": "node-personas"},
            {"source": "node-personas", "target": "node-end"}
        ]
    }


@pytest.fixture
def mock_workflow(valid_workflow_data):
    """Fixture: Mock Workflow object z valid data."""
    workflow = Workflow(
        id=uuid4(),
        name="Test Workflow",
        description="Test workflow for validation",
        canvas_data=valid_workflow_data,
        project_id=uuid4(),
        owner_id=uuid4(),
        status="draft"
    )
    return workflow


# ==================== GRAPH VALIDATION TESTS ====================

@pytest.mark.asyncio
async def test_valid_workflow_graph(validator, mock_workflow):
    """Test: Valid workflow graph passes validation."""
    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is True
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


@pytest.mark.asyncio
async def test_missing_start_node(validator, mock_workflow):
    """Test: Missing start node returns error."""
    # Remove start node
    mock_workflow.canvas_data["nodes"] = [
        n for n in mock_workflow.canvas_data["nodes"]
        if n["type"] != "start"
    ]

    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is False
    assert any("start" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_multiple_start_nodes(validator, mock_workflow):
    """Test: Multiple start nodes return error."""
    # Add second start node
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-start-2",
        "type": "start",
        "data": {"label": "Start 2", "config": {"trigger_type": "manual"}}
    })

    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is False
    assert any("start" in err.lower() and "2" in err for err in result.errors)


@pytest.mark.asyncio
async def test_missing_end_node(validator, mock_workflow):
    """Test: Missing end node returns error."""
    # Remove end node
    mock_workflow.canvas_data["nodes"] = [
        n for n in mock_workflow.canvas_data["nodes"]
        if n["type"] != "end"
    ]

    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is False
    assert any("end" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_cycle_detection(validator, mock_workflow):
    """Test: Cycle in graph is detected."""
    # Create cycle: personas -> survey -> personas
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-survey",
        "type": "create-survey",
        "data": {
            "label": "Survey",
            "config": {
                "survey_title": "Test Survey",
                "questions": [{"type": "text-long", "text": "Question 1"}]
            }
        }
    })

    # Add edges creating cycle
    mock_workflow.canvas_data["edges"] = [
        {"source": "node-start", "target": "node-personas"},
        {"source": "node-personas", "target": "node-survey"},
        {"source": "node-survey", "target": "node-personas"},  # CYCLE!
        {"source": "node-survey", "target": "node-end"}
    ]

    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is False
    assert any("cykl" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_orphaned_node_detection(validator, mock_workflow):
    """Test: Orphaned node (unreachable from start) is detected."""
    # Add orphaned node (no edges)
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-orphan",
        "type": "create-survey",
        "data": {
            "label": "Orphaned Survey",
            "config": {"survey_title": "Orphaned"}
        }
    })

    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is False
    assert any("orphan" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_disconnected_node_warning(validator, mock_workflow):
    """Test: Disconnected node (no edges at all) generates warning."""
    # Add disconnected node
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-disconnected",
        "type": "export-pdf",
        "data": {
            "label": "Disconnected PDF",
            "config": {"report_title": "Report"}
        }
    })

    result = await validator.validate_workflow_graph(mock_workflow)

    assert result.is_valid is False  # Also orphaned
    assert len(result.warnings) > 0
    assert any("disconnected" in warn.lower() for warn in result.warnings)


# ==================== NODE CONFIG VALIDATION TESTS ====================

@pytest.mark.asyncio
async def test_valid_node_configs(validator, mock_workflow):
    """Test: Valid node configs pass validation."""
    result = await validator.validate_node_configs(mock_workflow)

    assert result.is_valid is True
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_invalid_node_type(validator, mock_workflow):
    """Test: Invalid node type returns error."""
    # Add node with invalid type
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-invalid",
        "type": "invalid-type",
        "data": {"label": "Invalid", "config": {}}
    })

    result = await validator.validate_node_configs(mock_workflow)

    assert result.is_valid is False
    assert any("nieznany typ" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_missing_required_field(validator, mock_workflow):
    """Test: Missing required field returns error."""
    # Remove required field 'count' from personas node
    for node in mock_workflow.canvas_data["nodes"]:
        if node["type"] == "generate-personas":
            del node["data"]["config"]["count"]

    result = await validator.validate_node_configs(mock_workflow)

    assert result.is_valid is False
    assert any("count" in err.lower() and "required" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_invalid_value_range(validator, mock_workflow):
    """Test: Value out of range returns error."""
    # Set count to 150 (max allowed: 100)
    for node in mock_workflow.canvas_data["nodes"]:
        if node["type"] == "generate-personas":
            node["data"]["config"]["count"] = 150

    result = await validator.validate_node_configs(mock_workflow)

    assert result.is_valid is False
    assert any("count" in err.lower() and "100" in err for err in result.errors)


@pytest.mark.asyncio
async def test_mvp_disabled_node_warning(validator, mock_workflow):
    """Test: MVP disabled node type generates warning."""
    # Add 'wait' node (OUT OF SCOPE MVP)
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-wait",
        "type": "wait",
        "data": {
            "label": "Wait 1 hour",
            "config": {"duration_seconds": 3600}
        }
    })

    result = await validator.validate_node_configs(mock_workflow)

    assert result.is_valid is True  # Warning, nie error
    assert len(result.warnings) > 0
    assert any("out of scope" in warn.lower() for warn in result.warnings)


# ==================== DEPENDENCY CHECKS TESTS ====================

@pytest.mark.asyncio
async def test_valid_project_dependency(validator, mock_workflow, db_session, test_project):
    """Test: Valid project passes dependency check."""
    mock_workflow.project_id = test_project.id

    result = await validator.check_dependencies(mock_workflow, db_session)

    assert result.is_valid is True
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_missing_project_dependency(validator, mock_workflow, db_session):
    """Test: Missing project returns error."""
    # Set non-existent project_id
    mock_workflow.project_id = uuid4()

    result = await validator.check_dependencies(mock_workflow, db_session)

    assert result.is_valid is False
    assert any("projekt" in err.lower() and "nieaktywny" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_missing_personas_dependency(validator, mock_workflow, db_session, test_project):
    """Test: Missing personas for focus group returns error."""
    mock_workflow.project_id = test_project.id

    # Add focus group node z non-existent participant_ids
    mock_workflow.canvas_data["nodes"].append({
        "id": "node-fg",
        "type": "run-focus-group",
        "data": {
            "label": "Focus Group",
            "config": {
                "focus_group_title": "Product Discussion",
                "topics": ["Feature X", "Pricing"],
                "participant_ids": [str(uuid4()), str(uuid4())]  # Non-existent
            }
        }
    })

    result = await validator.check_dependencies(mock_workflow, db_session)

    assert result.is_valid is False
    assert any("personas nie znalezione" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_valid_personas_dependency(validator, mock_workflow, db_session, test_project, test_personas):
    """Test: Valid personas pass dependency check."""
    mock_workflow.project_id = test_project.id

    # Add focus group node z existing participant_ids
    participant_ids = [str(p.id) for p in test_personas[:5]]

    mock_workflow.canvas_data["nodes"].append({
        "id": "node-fg",
        "type": "run-focus-group",
        "data": {
            "label": "Focus Group",
            "config": {
                "focus_group_title": "Product Discussion",
                "topics": ["Feature X"],
                "participant_ids": participant_ids
            }
        }
    })

    result = await validator.check_dependencies(mock_workflow, db_session)

    assert result.is_valid is True
    assert len(result.errors) == 0


# ==================== COMBINED VALIDATION TESTS ====================

@pytest.mark.asyncio
async def test_validate_execution_readiness_success(validator, mock_workflow, db_session, test_project):
    """Test: Full validation passes dla valid workflow."""
    mock_workflow.project_id = test_project.id

    result = await validator.validate_execution_readiness(mock_workflow, db_session)

    assert result.is_valid is True
    assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_validate_execution_readiness_multiple_errors(validator, mock_workflow, db_session):
    """Test: Multiple validation errors are aggregated."""
    # Create workflow z multiple errors:
    # 1. Missing start node
    # 2. Missing project
    # 3. Invalid node config

    # Remove start node
    mock_workflow.canvas_data["nodes"] = [
        n for n in mock_workflow.canvas_data["nodes"]
        if n["type"] != "start"
    ]

    # Set non-existent project
    mock_workflow.project_id = uuid4()

    # Set invalid persona count
    for node in mock_workflow.canvas_data["nodes"]:
        if node["type"] == "generate-personas":
            node["data"]["config"]["count"] = 200  # > 100

    result = await validator.validate_execution_readiness(mock_workflow, db_session)

    assert result.is_valid is False
    assert len(result.errors) >= 3  # At least 3 errors


# ==================== EDGE CASES ====================

@pytest.mark.asyncio
async def test_empty_workflow(validator):
    """Test: Empty workflow (no nodes) returns error."""
    workflow = Workflow(
        id=uuid4(),
        name="Empty Workflow",
        canvas_data={"nodes": [], "edges": []},
        project_id=uuid4(),
        owner_id=uuid4(),
        status="draft"
    )

    result = await validator.validate_workflow_graph(workflow)

    assert result.is_valid is False
    assert any("co najmniej jeden node" in err.lower() for err in result.errors)


@pytest.mark.asyncio
async def test_workflow_with_only_start_end(validator, db_session, test_project):
    """Test: Workflow z tylko start+end nodes jest valid."""
    workflow = Workflow(
        id=uuid4(),
        name="Minimal Workflow",
        project_id=test_project.id,
        owner_id=uuid4(),
        canvas_data={
            "nodes": [
                {"id": "start", "type": "start", "data": {"label": "Start", "config": {}}},
                {"id": "end", "type": "end", "data": {"label": "End", "config": {}}}
            ],
            "edges": [
                {"source": "start", "target": "end"}
            ]
        },
        status="draft"
    )

    result = await validator.validate_execution_readiness(workflow, db_session)

    assert result.is_valid is True


@pytest.mark.asyncio
async def test_complex_workflow_50_nodes(validator, db_session, test_project):
    """Test: Complex workflow z 50 nodes (performance test)."""
    import time

    # Generate 50 nodes workflow
    nodes = [{"id": "start", "type": "start", "data": {"label": "Start", "config": {}}}]
    edges = []

    for i in range(48):
        nodes.append({
            "id": f"node-{i}",
            "type": "generate-personas",
            "data": {
                "label": f"Personas {i}",
                "config": {"count": 20}
            }
        })
        if i == 0:
            edges.append({"source": "start", "target": f"node-{i}"})
        else:
            edges.append({"source": f"node-{i-1}", "target": f"node-{i}"})

    nodes.append({"id": "end", "type": "end", "data": {"label": "End", "config": {}}})
    edges.append({"source": "node-47", "target": "end"})

    workflow = Workflow(
        id=uuid4(),
        name="Complex 50-node Workflow",
        project_id=test_project.id,
        owner_id=uuid4(),
        canvas_data={"nodes": nodes, "edges": edges},
        status="draft"
    )

    # Measure validation time
    start_time = time.time()
    result = await validator.validate_execution_readiness(workflow, db_session)
    elapsed = time.time() - start_time

    assert result.is_valid is True
    assert elapsed < 0.5  # Should complete in <500ms
```

## Fixtures Needed (in conftest.py)

```python
# tests/conftest.py

@pytest.fixture
async def test_project(db_session, test_user):
    """Create test project."""
    from app.models import Project

    project = Project(
        name="Test Project",
        description="Test project for workflows",
        owner_id=test_user.id,
        target_demographics={
            "age": {"min": 18, "max": 65},
            "gender": {"male": 50, "female": 50}
        }
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    return project


@pytest.fixture
async def test_personas(db_session, test_project):
    """Create 20 test personas."""
    from app.models import Persona

    personas = []
    for i in range(20):
        persona = Persona(
            project_id=test_project.id,
            name=f"Test Persona {i}",
            age=25 + i,
            gender="male" if i % 2 == 0 else "female",
            location="Warsaw",
            occupation=f"Occupation {i}",
            background=f"Background {i}",
            personality_traits=["trait1", "trait2"],
            values_and_attitudes=["value1"],
            jobs_to_be_done=["jtbd1"],
            needs_and_pain_points={"needs": [], "pain_points": []},
            demographic_segment={},
            generation_metadata={}
        )
        db_session.add(persona)
        personas.append(persona)

    await db_session.commit()

    return personas
```

## Running Tests

```bash
# Run all validator tests
pytest tests/unit/services/workflows/test_workflow_validator.py -v

# Run specific test
pytest tests/unit/services/workflows/test_workflow_validator.py::test_cycle_detection -v

# Run z coverage
pytest tests/unit/services/workflows/test_workflow_validator.py --cov=app.services.workflows.workflow_validator

# Run tylko graph validation tests
pytest tests/unit/services/workflows/test_workflow_validator.py -k "graph" -v

# Run tylko config validation tests
pytest tests/unit/services/workflows/test_workflow_validator.py -k "config" -v

# Run tylko dependency tests
pytest tests/unit/services/workflows/test_workflow_validator.py -k "dependency" -v
```

## Expected Coverage

- **Lines:** 95%+ (wszystkie main paths + edge cases)
- **Branches:** 90%+ (error paths, warning paths)
- **Functions:** 100% (każda publiczna metoda testowana)

## Next Steps

1. ✅ Create `tests/unit/services/workflows/test_workflow_validator.py` z powyższymi testami
2. ✅ Add fixtures do `tests/conftest.py` (`test_project`, `test_personas`)
3. ✅ Run tests: `pytest tests/unit/services/workflows/test_workflow_validator.py -v`
4. ✅ Check coverage: `pytest --cov=app.services.workflows.workflow_validator --cov-report=html`
5. ✅ Fix any failing tests
6. ✅ Review code coverage report (`htmlcov/index.html`)
