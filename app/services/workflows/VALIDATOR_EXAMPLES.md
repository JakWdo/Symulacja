# WorkflowValidator - Przykłady Użycia i Test Cases

## Przegląd

`WorkflowValidator` przeprowadza pre-flight validation workflow przed wykonaniem. Sprawdza:
1. **Graph structure** (DAG, cycles, orphaned nodes)
2. **Node configurations** (required fields, value ranges)
3. **External dependencies** (project, personas)

---

## Przykłady Użycia

### 1. Basic Usage - Validate Single Workflow

```python
from app.services.workflows import WorkflowValidator
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

async def validate_workflow_example(workflow_id: UUID, db: AsyncSession):
    """Przykład walidacji workflow przed execution."""
    from app.models.workflow import Workflow

    # 1. Pobierz workflow
    stmt = select(Workflow).where(Workflow.id == workflow_id)
    result = await db.execute(stmt)
    workflow = result.scalar_one()

    # 2. Zainicjalizuj validator
    validator = WorkflowValidator()

    # 3. Uruchom full validation
    validation_result = await validator.validate_execution_readiness(
        workflow=workflow,
        db=db
    )

    # 4. Sprawdź wynik
    if validation_result.is_valid:
        print("✅ Workflow jest ready to execute!")
        return True
    else:
        print("❌ Workflow ma błędy:")
        for error in validation_result.errors:
            print(f"  - {error}")

        if validation_result.warnings:
            print("⚠️  Ostrzeżenia:")
            for warning in validation_result.warnings:
                print(f"  - {warning}")

        return False
```

---

### 2. Granular Validation - Graph Only

```python
async def validate_graph_structure(workflow: Workflow):
    """Waliduj tylko strukturę grafu (bez DB checks)."""
    validator = WorkflowValidator()

    result = await validator.validate_workflow_graph(workflow)

    if not result.is_valid:
        print("Błędy grafu:")
        for error in result.errors:
            print(f"  {error}")

    return result
```

---

### 3. Granular Validation - Node Configs Only

```python
async def validate_node_configurations(workflow: Workflow):
    """Waliduj tylko konfiguracje nodes (bez DB checks)."""
    validator = WorkflowValidator()

    result = await validator.validate_node_configs(workflow)

    if not result.is_valid:
        print("Błędy konfiguracji nodes:")
        for error in result.errors:
            print(f"  {error}")

    return result
```

---

### 4. Granular Validation - Dependencies Only

```python
async def validate_dependencies(workflow: Workflow, db: AsyncSession):
    """Waliduj tylko external dependencies (project, personas)."""
    validator = WorkflowValidator()

    result = await validator.check_dependencies(workflow, db)

    if not result.is_valid:
        print("Błędy dependencies:")
        for error in result.errors:
            print(f"  {error}")

    return result
```

---

### 5. API Integration - Endpoint Example

```python
from fastapi import APIRouter, Depends, HTTPException
from app.services.workflows import WorkflowValidator, WorkflowService
from app.schemas.workflow import ValidationResult

router = APIRouter()

@router.post("/workflows/{workflow_id}/validate", response_model=ValidationResult)
async def validate_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint do walidacji workflow przed execution.

    Returns:
        ValidationResult z errors i warnings

    Raises:
        404: Workflow nie znaleziony
        403: Brak uprawnień
    """
    # 1. Pobierz workflow (z auth check)
    workflow_service = WorkflowService(db)
    workflow = await workflow_service.get_workflow_by_id(
        workflow_id=workflow_id,
        user_id=current_user.id
    )

    # 2. Validate
    validator = WorkflowValidator()
    result = await validator.validate_execution_readiness(
        workflow=workflow,
        db=db
    )

    return result
```

---

## Test Cases

### Test Case 1: Valid Workflow (Happy Path)

**Input:**
```json
{
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
```

**Expected Result:**
```python
ValidationResult(
    is_valid=True,
    errors=[],
    warnings=[]
)
```

---

### Test Case 2: Missing Start Node

**Input:**
```json
{
  "nodes": [
    {
      "id": "node-personas",
      "type": "generate-personas",
      "data": {"label": "Generate Personas", "config": {"count": 20}}
    },
    {
      "id": "node-end",
      "type": "end",
      "data": {"label": "End", "config": {}}
    }
  ],
  "edges": [
    {"source": "node-personas", "target": "node-end"}
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=["Workflow musi mieć dokładnie jeden node typu 'start'"],
    warnings=[]
)
```

---

### Test Case 3: Cycle Detection

**Input:**
```json
{
  "nodes": [
    {"id": "node-1", "type": "start", "data": {"label": "Start", "config": {}}},
    {"id": "node-2", "type": "generate-personas", "data": {"label": "Personas", "config": {"count": 20}}},
    {"id": "node-3", "type": "create-survey", "data": {"label": "Survey", "config": {"survey_title": "Test"}}},
    {"id": "node-4", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    {"source": "node-1", "target": "node-2"},
    {"source": "node-2", "target": "node-3"},
    {"source": "node-3", "target": "node-2"},  // CYCLE!
    {"source": "node-3", "target": "node-4"}
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=["Workflow zawiera cykl: node-2 → node-3 → node-2"],
    warnings=[]
)
```

---

### Test Case 4: Orphaned Node

**Input:**
```json
{
  "nodes": [
    {"id": "node-start", "type": "start", "data": {"label": "Start", "config": {}}},
    {"id": "node-personas", "type": "generate-personas", "data": {"label": "Personas", "config": {"count": 20}}},
    {"id": "node-orphan", "type": "create-survey", "data": {"label": "Orphaned Survey", "config": {"survey_title": "Test"}}},
    {"id": "node-end", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    {"source": "node-start", "target": "node-personas"},
    {"source": "node-personas", "target": "node-end"}
    // node-orphan ma 0 edges!
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=["Orphaned nodes (niedostępne z start): node-orphan"],
    warnings=["Disconnected nodes (brak edges): node-orphan"]
)
```

---

### Test Case 5: Invalid Node Config (Missing Required Field)

**Input:**
```json
{
  "nodes": [
    {"id": "node-start", "type": "start", "data": {"label": "Start", "config": {}}},
    {
      "id": "node-personas",
      "type": "generate-personas",
      "data": {
        "label": "Generate Personas",
        "config": {
          // BRAK required field "count"!
          "demographic_preset": "millennials"
        }
      }
    },
    {"id": "node-end", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    {"source": "node-start", "target": "node-personas"},
    {"source": "node-personas", "target": "node-end"}
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=["Node 'Generate Personas' (node-personas, typ: generate-personas): count - field required"],
    warnings=[]
)
```

---

### Test Case 6: Invalid Value Range

**Input:**
```json
{
  "nodes": [
    {"id": "node-start", "type": "start", "data": {"label": "Start", "config": {}}},
    {
      "id": "node-personas",
      "type": "generate-personas",
      "data": {
        "label": "Generate Personas",
        "config": {
          "count": 150,  // MAX allowed: 100 (ge=1, le=100)
          "demographic_preset": "millennials"
        }
      }
    },
    {"id": "node-end", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    {"source": "node-start", "target": "node-personas"},
    {"source": "node-personas", "target": "node-end"}
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=["Node 'Generate Personas' (node-personas, typ: generate-personas): count - ensure this value is less than or equal to 100"],
    warnings=[]
)
```

---

### Test Case 7: Missing Dependency (Personas)

**Input:**
```json
{
  "nodes": [
    {"id": "node-start", "type": "start", "data": {"label": "Start", "config": {}}},
    {
      "id": "node-fg",
      "type": "run-focus-group",
      "data": {
        "label": "Focus Group",
        "config": {
          "focus_group_title": "Product Discussion",
          "topics": ["Feature X", "Pricing"],
          "participant_ids": [
            "00000000-0000-0000-0000-000000000001",  // Persona NIE ISTNIEJE!
            "00000000-0000-0000-0000-000000000002"
          ]
        }
      }
    },
    {"id": "node-end", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    {"source": "node-start", "target": "node-fg"},
    {"source": "node-fg", "target": "node-end"}
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=[
        "Node 'Focus Group' (node-fg): Personas nie znalezione: "
        "00000000-0000-0000-0000-000000000001, 00000000-0000-0000-0000-000000000002"
    ],
    warnings=[]
)
```

---

### Test Case 8: MVP Disabled Node Type (Warning)

**Input:**
```json
{
  "nodes": [
    {"id": "node-start", "type": "start", "data": {"label": "Start", "config": {}}},
    {
      "id": "node-wait",
      "type": "wait",  // OUT OF SCOPE MVP
      "data": {
        "label": "Wait 1 hour",
        "config": {"duration_seconds": 3600}
      }
    },
    {"id": "node-end", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    {"source": "node-start", "target": "node-wait"},
    {"source": "node-wait", "target": "node-end"}
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=True,  # Warning, nie error
    errors=[],
    warnings=["Node 'Wait 1 hour' (node-wait): Typ 'wait' jest OUT OF SCOPE dla MVP"]
)
```

---

### Test Case 9: Multiple Errors (Combined)

**Input:**
```json
{
  "nodes": [
    // Brak Start node!
    {
      "id": "node-personas",
      "type": "generate-personas",
      "data": {
        "label": "Generate Personas",
        "config": {"count": 200}  // PRZEKROCZENIE LIMITU (max 100)
      }
    },
    {
      "id": "node-orphan",
      "type": "create-survey",
      "data": {"label": "Orphaned", "config": {"survey_title": "Test"}}
    },
    {"id": "node-end", "type": "end", "data": {"label": "End", "config": {}}}
  ],
  "edges": [
    // node-personas ma 0 edges (disconnected)
    // node-orphan ma 0 edges (orphaned)
  ]
}
```

**Expected Result:**
```python
ValidationResult(
    is_valid=False,
    errors=[
        "Workflow musi mieć dokładnie jeden node typu 'start'",
        "Orphaned nodes (niedostępne z start): node-personas, node-orphan, node-end",
        "Node 'Generate Personas' (node-personas, typ: generate-personas): count - ensure this value is less than or equal to 100"
    ],
    warnings=[
        "Disconnected nodes (brak edges): node-personas, node-orphan, node-end"
    ]
)
```

---

## Performance Considerations

### Time Complexity

1. **Graph Validation** (`validate_workflow_graph`):
   - Cycle detection (Kahn's algorithm): **O(V + E)** gdzie V = nodes, E = edges
   - Reachability check (BFS): **O(V + E)**
   - Disconnected nodes: **O(V + E)**
   - **Total: O(V + E)** - liniowy względem wielkości grafu

2. **Node Config Validation** (`validate_node_configs`):
   - Iteracja przez nodes: **O(V)**
   - Pydantic validation per node: **O(1)** (constant time per node)
   - **Total: O(V)** - liniowy względem liczby nodes

3. **Dependency Checks** (`check_dependencies`):
   - Project lookup: **O(1)** (single DB query)
   - Personas lookup: **O(N)** gdzie N = liczba participant_ids (single `IN` query)
   - **Total: O(V × N)** gdzie N = avg participant_ids per focus group node

### Memory Usage

- **Graph algorithms:** O(V + E) (adjacency list, visited sets)
- **Validation results:** O(V) (error per node w worst case)
- **Total:** O(V + E) - liniowy

### Recommended Limits (MVP)

- **Max nodes per workflow:** 50 nodes (Pro tier: 20, Free: 5)
- **Max edges:** ~100 edges (2 edges per node average)
- **Validation time:** <200ms dla 50 nodes, <50ms dla 20 nodes

---

## Error Handling

### Exception Handling w Validator

```python
async def safe_validate(workflow: Workflow, db: AsyncSession) -> ValidationResult:
    """Validate z exception handling."""
    validator = WorkflowValidator()

    try:
        result = await validator.validate_execution_readiness(workflow, db)
        return result
    except Exception as e:
        logger.error(f"Validation error for workflow {workflow.id}: {e}", exc_info=True)

        # Return ValidationResult z internal error
        return ValidationResult(
            is_valid=False,
            errors=[f"Internal validation error: {str(e)}"],
            warnings=[]
        )
```

---

## Integration with Workflow Execution

```python
from app.services.workflows import WorkflowService, WorkflowValidator

async def execute_workflow_safe(workflow_id: UUID, user_id: UUID, db: AsyncSession):
    """Execute workflow z pre-flight validation."""
    # 1. Pobierz workflow
    workflow_service = WorkflowService(db)
    workflow = await workflow_service.get_workflow_by_id(workflow_id, user_id)

    # 2. Pre-flight validation
    validator = WorkflowValidator()
    validation = await validator.validate_execution_readiness(workflow, db)

    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Workflow validation failed",
                "errors": validation.errors,
                "warnings": validation.warnings
            }
        )

    # 3. Proceed z execution (jeśli valid)
    from app.services.workflows.workflow_executor import WorkflowExecutor
    executor = WorkflowExecutor(db)
    execution = await executor.execute(workflow, user_id)

    return execution
```

---

## Debugging Tips

### 1. Włącz Debug Logging

```python
import logging
logging.getLogger("app.services.workflows.workflow_validator").setLevel(logging.DEBUG)
```

### 2. Inspect Canvas Data

```python
def debug_workflow_structure(workflow: Workflow):
    """Debug helper - wyświetl strukturę workflow."""
    print(f"Workflow: {workflow.name}")
    print(f"Nodes ({len(workflow.canvas_data['nodes'])}):")
    for node in workflow.canvas_data['nodes']:
        print(f"  - {node['id']} ({node['type']}): {node.get('data', {}).get('label')}")

    print(f"\nEdges ({len(workflow.canvas_data['edges'])}):")
    for edge in workflow.canvas_data['edges']:
        print(f"  - {edge['source']} → {edge['target']}")
```

### 3. Validate Incrementally

```python
async def debug_validate(workflow: Workflow, db: AsyncSession):
    """Validate step-by-step dla debugging."""
    validator = WorkflowValidator()

    print("1. Graph validation...")
    graph_result = await validator.validate_workflow_graph(workflow)
    print(f"   Valid: {graph_result.is_valid}, Errors: {len(graph_result.errors)}")

    print("2. Config validation...")
    config_result = await validator.validate_node_configs(workflow)
    print(f"   Valid: {config_result.is_valid}, Errors: {len(config_result.errors)}")

    print("3. Dependencies check...")
    deps_result = await validator.check_dependencies(workflow, db)
    print(f"   Valid: {deps_result.is_valid}, Errors: {len(deps_result.errors)}")
```

---

## Summary

`WorkflowValidator` to serwis walidacji workflow który:
- ✅ Wykrywa błędy grafu (cycles, orphaned nodes)
- ✅ Waliduje konfiguracje nodes (Pydantic schemas)
- ✅ Sprawdza external dependencies (DB queries)
- ✅ Zwraca user-friendly error messages
- ✅ O(V + E) time complexity - wydajny dla 50+ nodes
- ✅ Separation of concerns - graph / config / dependencies

**Next Steps:**
1. Dodaj unit tests (`tests/unit/services/workflows/test_workflow_validator.py`)
2. Dodaj API endpoint `/workflows/{id}/validate`
3. Zintegruj z workflow executor (pre-flight check)
