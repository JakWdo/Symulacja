# WorkflowExecutor - Przykłady Użycia

## Przegląd

**WorkflowExecutor** - silnik wykonania workflow dla Sight Workflow Builder.

**Status:** MVP Ready (podstawowe node types zaimplementowane)

**Główne komponenty:**
- `WorkflowExecutor` - główny orchestrator
- `NodeExecutor` (base) - abstrakcyjna klasa dla executorów węzłów
- Node executors - konkretne implementacje per typ węzła

---

## Architektura

### Flow Wykonania

```
1. Load Workflow (auth check)
      ↓
2. Pre-flight Validation (WorkflowValidator)
      ↓
3. Create WorkflowExecution record
      ↓
4. Topological Sort (execution order)
      ↓
5. Execute Nodes Sequentially
   ├─ StartExecutor → GeneratePersonasExecutor → RunFocusGroupExecutor → EndExecutor
   └─ (dla każdego node: execute() → store result → update execution record)
      ↓
6. Mark Completed / Failed
```

### Node Types (MVP)

**Zaimplementowane:**
- ✅ `start` - StartExecutor
- ✅ `end` - EndExecutor
- ✅ `generate-personas` - GeneratePersonasExecutor
- ✅ `run-focus-group` - RunFocusGroupExecutor
- ✅ `decision` - DecisionExecutor

**Stubs (OUT OF SCOPE dla MVP):**
- ⚠️ `create-survey` - NotImplementedError
- ⚠️ `analyze-results` - NotImplementedError
- ⚠️ `export-pdf` - NotImplementedError

---

## API Użycia

### Podstawowe Użycie

```python
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.workflows import WorkflowExecutor

async def execute_workflow_example(
    db: AsyncSession,
    workflow_id: UUID,
    user_id: UUID
):
    """Wykonaj workflow."""
    executor = WorkflowExecutor(db)

    try:
        execution = await executor.execute_workflow(
            workflow_id=workflow_id,
            user_id=user_id
        )

        print(f"Workflow completed: {execution.status}")
        print(f"Results: {execution.result_data}")

        return execution

    except ValueError as e:
        # Validation error
        print(f"Validation failed: {e}")
        raise

    except NotImplementedError as e:
        # Node type not implemented
        print(f"Feature not available: {e}")
        raise

    except Exception as e:
        # Execution error
        print(f"Workflow failed: {e}")
        raise
```

### API Endpoint Integration

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.workflows import WorkflowExecutor
from app.schemas.workflow import WorkflowExecutionResponse

router = APIRouter()

@router.post("/workflows/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> WorkflowExecutionResponse:
    """Execute workflow endpoint.

    Background task execution:
    1. Validate workflow
    2. Create execution record
    3. Execute nodes sequentially
    4. Return execution results
    """
    executor = WorkflowExecutor(db)

    try:
        execution = await executor.execute_workflow(
            workflow_id=workflow_id,
            user_id=current_user.id
        )

        return WorkflowExecutionResponse(
            id=execution.id,
            workflow_id=execution.workflow_id,
            status=execution.status,
            result_data=execution.result_data,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
        )

    except ValueError as e:
        # Validation failed
        raise HTTPException(status_code=400, detail=str(e))

    except NotImplementedError as e:
        # Feature not implemented
        raise HTTPException(status_code=501, detail=str(e))

    except Exception as e:
        # Execution failed
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {e}")
```

---

## Execution Context

**Struktura:**

```python
execution_context = {
    'project_id': UUID,           # ID projektu
    'workflow_id': UUID,          # ID workflow
    'user_id': UUID,              # ID użytkownika (auth)
    'results': {                  # Wyniki poprzednich węzłów
        'node_1_id': {
            'persona_ids': [...],
            'count': 20,
            'demographics': {...}
        },
        'node_2_id': {
            'focus_group_id': UUID,
            'status': 'completed',
            'participant_count': 20
        }
    }
}
```

**Użycie w Node Executors:**

```python
class MyNodeExecutor(NodeExecutor):
    async def execute(self, node: dict, execution_context: dict) -> dict:
        # Access previous results
        previous_results = execution_context.get('results', {})

        # Get persona_ids from previous generate-personas node
        for result in previous_results.values():
            if 'persona_ids' in result:
                persona_ids = result['persona_ids']
                break

        # Execute logic...

        return {'my_result': 'value'}
```

---

## Node Executor Examples

### 1. StartExecutor (Simple)

```python
class StartExecutor(NodeExecutor):
    async def execute(self, node, execution_context):
        logger.info(f"Workflow {execution_context['workflow_id']} started")

        return {
            'node_type': 'start',
            'status': 'initialized',
            'workflow_id': str(execution_context['workflow_id'])
        }
```

**Output:**
```json
{
  "node_type": "start",
  "status": "initialized",
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 2. GeneratePersonasExecutor (Complex)

```python
class GeneratePersonasExecutor(NodeExecutor):
    async def execute(self, node, execution_context):
        config = GeneratePersonasNodeConfig(**node['data']['config'])

        # 1. Load project
        project = await self._load_project(execution_context['project_id'])

        # 2. Create allocation plan (orchestration)
        orchestrator = PersonaOrchestrationService()
        allocation_plan = await orchestrator.create_persona_allocation_plan(
            target_demographics=project.target_demographics,
            num_personas=config.count
        )

        # 3. Generate personas (per group)
        # MVP: Stub - placeholder persona IDs
        persona_ids = [str(uuid4()) for _ in range(config.count)]

        return {
            'persona_ids': persona_ids,
            'count': len(persona_ids),
            'groups': [...allocation_plan.groups...]
        }
```

**Input Config:**
```json
{
  "count": 20,
  "demographic_preset": "poland_urban_millennials",
  "project_description": "Product testing for mobile app"
}
```

**Output:**
```json
{
  "persona_ids": ["uuid1", "uuid2", ...],
  "count": 20,
  "demographics": {...},
  "groups": [
    {
      "count": 6,
      "demographics": {"age": "25-34", "gender": "kobieta"},
      "brief": "Młode profesjonalistki..."
    }
  ]
}
```

---

### 3. RunFocusGroupExecutor (Integration)

```python
class RunFocusGroupExecutor(NodeExecutor):
    async def execute(self, node, execution_context):
        config = RunFocusGroupNodeConfig(**node['data']['config'])

        # 1. Get participant_ids (from config or previous node)
        participant_ids = self._get_participant_ids(config, execution_context)

        # 2. Create FocusGroup record
        focus_group = FocusGroup(
            project_id=execution_context['project_id'],
            persona_ids=participant_ids,
            questions=self._generate_questions(config.topics)
        )
        self.db.add(focus_group)
        await self.db.commit()

        # 3. Run focus group (FocusGroupService)
        fg_service = FocusGroupServiceLangChain()
        result = await fg_service.run_focus_group(self.db, focus_group.id)

        return {
            'focus_group_id': str(focus_group.id),
            'status': result['status'],
            'participant_count': len(participant_ids)
        }
```

**Input Config:**
```json
{
  "name": "Product Feedback Session",
  "topics": ["Product features", "Pricing", "User experience"],
  "participant_ids": null  // Auto-fill from previous generate-personas node
}
```

**Output:**
```json
{
  "focus_group_id": "uuid",
  "status": "completed",
  "participant_count": 20,
  "questions": ["What are your thoughts on product features?", ...],
  "total_execution_time_ms": 45000
}
```

---

### 4. DecisionExecutor (Conditional)

```python
class DecisionExecutor(NodeExecutor):
    async def execute(self, node, execution_context):
        config = DecisionNodeConfig(**node['data']['config'])
        condition = config.condition  # e.g., "persona_count > 15"

        # Build safe eval context
        eval_context = {
            'persona_count': len(execution_context['results']['node_1']['persona_ids']),
            'len': len,
            'True': True,
            'False': False
        }

        # Safe eval
        result = eval(condition, {"__builtins__": {}}, eval_context)
        branch = 'true' if result else 'false'

        return {
            'condition': condition,
            'result': bool(result),
            'branch_taken': branch
        }
```

**Input Config:**
```json
{
  "condition": "persona_count > 15"
}
```

**Output:**
```json
{
  "condition": "persona_count > 15",
  "result": true,
  "branch_taken": "true",
  "evaluation_context": {
    "persona_count": 20
  }
}
```

---

## Error Handling

### Validation Errors

```python
try:
    execution = await executor.execute_workflow(workflow_id, user_id)
except ValueError as e:
    # Workflow validation failed
    print(f"Invalid workflow: {e}")
    # Example: "Workflow zawiera cykl: node_1 → node_2 → node_1"
```

### Not Implemented Errors

```python
try:
    execution = await executor.execute_workflow(workflow_id, user_id)
except NotImplementedError as e:
    # Feature OUT OF SCOPE dla MVP
    print(f"Feature not available: {e}")
    # Example: "Survey creation is OUT OF SCOPE for MVP"
```

### Execution Errors

```python
try:
    execution = await executor.execute_workflow(workflow_id, user_id)
except Exception as e:
    # Node execution failed
    print(f"Workflow failed: {e}")
    # Workflow marked as 'failed' in DB
    # Error message stored in execution.error_message
```

---

## Performance

**Targets:**
- Small workflow (3-5 nodes): <2 min
- Medium workflow (10-15 nodes): <10 min
- Large workflow (20+ nodes): <30 min

**Current Implementation:**
- Sequential execution (MVP)
- No parallel processing
- Future: Parallel execution per layer (topological sort)

---

## Integration TODOs

### 1. Full Persona Generation Integration

**Current:** Placeholder persona IDs (stub)

**TODO:**
```python
# In GeneratePersonasExecutor
for group in allocation_plan.groups:
    # 1. Create SegmentDefinition
    segment = SegmentDefinition(...)

    # 2. Generate personas using PersonaGenerator
    for _ in range(group.count):
        prompt, response = await generator.generate_persona_from_segment(
            segment_id=segment.id,
            segment_name=group.segment_characteristics[0],
            segment_context=group.brief,
            demographics_constraints=group.demographics
        )

        # 3. Parse response to Persona model
        persona = Persona(**response)
        self.db.add(persona)

    await self.db.commit()
```

**Blocker:** PersonaGenerator.generate_persona_from_segment() returns (prompt, response) tuple, not Persona model.

---

### 2. Survey Integration

**Current:** NotImplementedError stub

**TODO:**
```python
# Create SurveyExecutor
class CreateSurveyExecutor(NodeExecutor):
    async def execute(self, node, execution_context):
        config = CreateSurveyNodeConfig(**node['data']['config'])

        # 1. Create Survey record
        survey = Survey(
            project_id=execution_context['project_id'],
            title=config.title,
            questions=config.questions
        )

        # 2. Generate responses (if auto_generate=True)
        if config.auto_generate_responses:
            survey_service = SurveyService()
            await survey_service.generate_responses(survey.id)

        return {'survey_id': str(survey.id)}
```

**Blocker:** SurveyService may not exist yet.

---

### 3. Results Analysis

**Current:** NotImplementedError stub

**TODO:**
```python
# Create AnalyzeResultsExecutor
class AnalyzeResultsExecutor(NodeExecutor):
    async def execute(self, node, execution_context):
        # 1. Get focus_group_id from previous node
        fg_id = execution_context['results']['fg_node']['focus_group_id']

        # 2. Analyze using LLM
        analysis_service = AnalysisService()
        insights = await analysis_service.extract_insights(fg_id)

        return {
            'insights': insights,
            'sentiment': {...},
            'themes': [...]
        }
```

**Blocker:** AnalysisService not implemented.

---

## Testing

### Unit Tests

```python
# tests/unit/services/workflows/test_workflow_executor.py

import pytest
from uuid import uuid4
from app.services.workflows import WorkflowExecutor

@pytest.mark.asyncio
async def test_execute_simple_workflow(db_session, test_workflow):
    """Test execution of simple workflow (start → end)."""
    executor = WorkflowExecutor(db_session)

    execution = await executor.execute_workflow(
        workflow_id=test_workflow.id,
        user_id=test_workflow.owner_id
    )

    assert execution.status == 'completed'
    assert 'start_node_id' in execution.result_data
    assert 'end_node_id' in execution.result_data

@pytest.mark.asyncio
async def test_validation_failure(db_session, invalid_workflow):
    """Test workflow with validation errors."""
    executor = WorkflowExecutor(db_session)

    with pytest.raises(ValueError, match="validation failed"):
        await executor.execute_workflow(
            workflow_id=invalid_workflow.id,
            user_id=invalid_workflow.owner_id
        )
```

---

## Monitoring & Debugging

### Logs

```python
# Example log output
INFO: Starting execution of workflow 550e8400-e29b-41d4-a716-446655440000
INFO: Loaded workflow 'Product Testing Flow' (project_id=...)
INFO: Workflow validation passed
INFO: Created WorkflowExecution a1b2c3d4-...
INFO: Execution order determined: 5 nodes (start_node, generate_node, ...)
INFO: [1/5] Executing node 'Start' (id=start_node, type=start)
INFO: Node 'Start' completed successfully
INFO: [2/5] Executing node 'Generate Personas' (id=generate_node, type=generate-personas)
INFO: Generating 20 personas for project ...
INFO: Allocation plan created: 3 groups
INFO: Generated 20 placeholder personas
INFO: Node 'Generate Personas' completed successfully
...
INFO: Workflow 550e8400... completed successfully (5 nodes executed)
```

### Metrics

```python
# In production, add metrics tracking:
from prometheus_client import Histogram

workflow_execution_time = Histogram(
    'workflow_execution_seconds',
    'Workflow execution time',
    ['workflow_id', 'status']
)

# In execute_workflow():
with workflow_execution_time.labels(
    workflow_id=str(workflow_id),
    status=execution.status
).time():
    # ... execution logic ...
```

---

## Future Enhancements

### v1.1 Features

1. **Parallel Execution**
   - Execute independent nodes in parallel
   - Topological sort per layer
   - Target: 2-3x speedup for large workflows

2. **Conditional Branching**
   - Full support dla decision nodes
   - Multiple branches (not just true/false)

3. **Loop Support**
   - Iterate over collections
   - While loops with conditions

4. **Error Recovery**
   - Retry failed nodes
   - Rollback strategies
   - Partial workflow resumption

5. **Progress Tracking**
   - Real-time progress updates (websockets)
   - Estimated time remaining
   - Node-level status

---

## Kontakt

**Pytania?** Zobacz:
- `docs/workflows/IMPLEMENTATION_REPORT.md` - Implementation report and architecture
- `app/services/workflows/workflow_validator.py` - Validation logic
- `app/models/workflow.py` - Data models
