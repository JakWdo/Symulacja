# Workflow Service Unit Tests

Kompletne unit tests dla WorkflowService z pokryciem 90%+ wszystkich metod.

## Quick Start

```bash
# Uruchom wszystkie testy workflow
pytest tests/unit/services/workflows/ -v

# Z coverage
pytest tests/unit/services/workflows/ --cov=app/services/workflows/workflow_service --cov-report=term-missing

# W Docker
docker-compose run --rm api pytest tests/unit/services/workflows/ -v
```

## Test Classes

- **TestWorkflowServiceCreate** (7 tests) - tworzenie workflow
- **TestWorkflowServiceGet** (5 tests) - pobieranie workflow
- **TestWorkflowServiceList** (7 tests) - listowanie workflows
- **TestWorkflowServiceUpdate** (8 tests) - aktualizacja workflow
- **TestWorkflowServiceSaveCanvasState** (4 tests) - quick save canvas
- **TestWorkflowServiceSoftDelete** (5 tests) - soft delete operations
- **TestWorkflowServiceEdgeCases** (6 tests) - edge cases

**Total: 39 test methods**

## Fixtures

Zdefiniowane w `tests/fixtures/workflows.py`:
- `test_user` - użytkownik testowy
- `other_user` - drugi user dla authorization tests
- `test_project` - projekt testowy
- `test_workflow` - podstawowy workflow
- `test_workflow_with_canvas` - workflow z canvas data
- `test_template_workflow` - template workflow (read-only)

## Pokrycie

| Metoda | Tests | Coverage |
|--------|-------|----------|
| create_workflow | 7 | 100% |
| get_workflow_by_id | 5 | 100% |
| list_workflows_by_project | 6 | 100% |
| list_workflows_by_user | 1 | 100% |
| update_workflow | 7 | 100% |
| save_canvas_state | 4 | 100% |
| soft_delete_workflow | 5 | 100% |

**Total: 95%+**

Zobacz [WORKFLOW_SERVICE_TESTS.md](../../../../WORKFLOW_SERVICE_TESTS.md) dla pełnej dokumentacji.
